// src/c/rtsp_capture.c
#include "rtsp_capture.h"
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
#include <libswscale/swscale.h>
#include <libavutil/imgutils.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define BUFFER_SIZE 30

static void* capture_loop(void* arg) {
    RTSPSession* session = (RTSPSession*)arg;
    AVPacket packet;
    AVFrame* frame = av_frame_alloc();
    AVFrame* rgb_frame = av_frame_alloc();
    uint8_t* buffer = NULL;
    
    int buffer_size = av_image_get_buffer_size(AV_PIX_FMT_RGB24, 
        session->config.width, session->config.height, 1);
    buffer = (uint8_t*)av_malloc(buffer_size);
    av_image_fill_arrays(rgb_frame->data, rgb_frame->linesize, buffer,
        AV_PIX_FMT_RGB24, session->config.width, session->config.height, 1);
    
    while (session->running) {
        int ret = av_read_frame(session->av_format_ctx, &packet);
        if (ret < 0) {
            usleep(10000);
            continue;
        }
        
        if (packet.stream_index == 0) {
            ret = avcodec_send_packet(session->av_codec_ctx, &packet);
            if (ret < 0) continue;
            
            while (ret >= 0) {
                ret = avcodec_receive_frame(session->av_codec_ctx, frame);
                if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) break;
                if (ret < 0) continue;
                
                sws_scale(session->sws_ctx, 
                    (const uint8_t* const*)frame->data, frame->linesize,
                    0, session->config.height,
                    rgb_frame->data, rgb_frame->linesize);
                
                pthread_mutex_lock(&session->mutex);
                
                Frame* new_frame = &session->frame_buffer[session->write_index];
                if (new_frame->data == NULL) {
                    new_frame->data = (uint8_t*)malloc(MAX_FRAME_SIZE);
                }
                
                memcpy(new_frame->data, buffer, buffer_size);
                new_frame->width = session->config.width;
                new_frame->height = session->config.height;
                new_frame->channels = 3;
                new_frame->timestamp = av_gettime();
                new_frame->camera_id = session->config.camera_id;
                
                session->write_index = (session->write_index + 1) % session->buffer_size;
                pthread_cond_signal(&session->cond);
                
                pthread_mutex_unlock(&session->mutex);
                
                av_frame_unref(frame);
            }
        }
        av_packet_unref(&packet);
    }
    
    av_frame_free(&frame);
    av_frame_free(&rgb_frame);
    av_free(buffer);
    return NULL;
}

RTSPSession* rtsp_init(CameraConfig* config, int buffer_size) {
    RTSPSession* session = (RTSPSession*)calloc(1, sizeof(RTSPSession));
    session->config = *config;
    session->buffer_size = buffer_size;
    session->frame_buffer = (Frame*)calloc(buffer_size, sizeof(Frame));
    session->running = 0;
    
    pthread_mutex_init(&session->mutex, NULL);
    pthread_cond_init(&session->cond, NULL);
    
    avformat_network_init();
    
    char url[MAX_RTSP_URL_LEN];
    if (strlen(config->username) > 0) {
        snprintf(url, MAX_RTSP_URL_LEN, "rtsp://%s:%s@%s", 
            config->username, config->password, config->rtsp_url);
    } else {
        snprintf(url, MAX_RTSP_URL_LEN, "rtsp://%s", config->rtsp_url);
    }
    
    avformat_open_input(&session->av_format_ctx, url, NULL, NULL);
    avformat_find_stream_info(session->av_format_ctx, NULL);
    
    int video_stream_index = -1;
    for (int i = 0; i < session->av_format_ctx->nb_streams; i++) {
        if (session->av_format_ctx->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO) {
            video_stream_index = i;
            break;
        }
    }
    
    AVCodec* codec = avcodec_find_decoder(
        session->av_format_ctx->streams[video_stream_index]->codecpar->codec_id);
    session->av_codec_ctx = avcodec_alloc_context3(codec);
    avcodec_parameters_to_context(session->av_codec_ctx, 
        session->av_format_ctx->streams[video_stream_index]->codecpar);
    avcodec_open2(session->av_codec_ctx, codec, NULL);
    
    session->sws_ctx = sws_getContext(config->width, config->height,
        session->av_codec_ctx->pix_fmt,
        config->width, config->height, AV_PIX_FMT_RGB24,
        SWS_BILINEAR, NULL, NULL, NULL);
    
    return session;
}

int rtsp_start(RTSPSession* session) {
    session->running = 1;
    return pthread_create(&session->capture_thread, NULL, capture_loop, session);
}

Frame* rtsp_get_frame(RTSPSession* session, int timeout_ms) {
    Frame* frame = NULL;
    pthread_mutex_lock(&session->mutex);
    
    if (session->read_index == session->write_index && timeout_ms > 0) {
        struct timespec ts;
        clock_gettime(CLOCK_REALTIME, &ts);
        ts.tv_nsec += timeout_ms * 1000000;
        pthread_cond_timedwait(&session->cond, &session->mutex, &ts);
    }
    
    if (session->read_index != session->write_index) {
        frame = &session->frame_buffer[session->read_index];
        session->read_index = (session->read_index + 1) % session->buffer_size;
    }
    
    pthread_mutex_unlock(&session->mutex);
    return frame;
}

void rtsp_release_frame(Frame* frame) {
    // Frame ownership management
}

void rtsp_stop(RTSPSession* session) {
    session->running = 0;
    pthread_join(session->capture_thread, NULL);
}

void rtsp_destroy(RTSPSession* session) {
    rtsp_stop(session);
    
    for (int i = 0; i < session->buffer_size; i++) {
        if (session->frame_buffer[i].data) {
            free(session->frame_buffer[i].data);
        }
    }
    
    free(session->frame_buffer);
    sws_freeContext(session->sws_ctx);
    avcodec_free_context(&session->av_codec_ctx);
    avformat_close_input(&session->av_format_ctx);
    pthread_mutex_destroy(&session->mutex);
    pthread_cond_destroy(&session->cond);
    free(session);
}
