// src/c/rtsp_capture.h
#ifndef RTSP_CAPTURE_H
#define RTSP_CAPTURE_H

#include <pthread.h>
#include "../../include/common.h"

typedef struct {
    CameraConfig config;
    Frame* frame_buffer;
    int buffer_size;
    int write_index;
    int read_index;
    pthread_mutex_t mutex;
    pthread_cond_t cond;
    int running;
    pthread_t capture_thread;
    void* av_format_ctx;
    void* av_codec_ctx;
    void* sws_ctx;
} RTSPSession;

RTSPSession* rtsp_init(CameraConfig* config, int buffer_size);
int rtsp_start(RTSPSession* session);
Frame* rtsp_get_frame(RTSPSession* session, int timeout_ms);
void rtsp_release_frame(Frame* frame);
void rtsp_stop(RTSPSession* session);
void rtsp_destroy(RTSPSession* session);

#endif
