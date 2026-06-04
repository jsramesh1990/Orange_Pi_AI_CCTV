// include/common.h
#ifndef COMMON_H
#define COMMON_H

#include <stdint.h>
#include <stdbool.h>
#include <pthread.h>

#define MAX_CAMERAS 8
#define MAX_FRAME_SIZE 1920 * 1080 * 3
#define MAX_RTSP_URL_LEN 512
#define MAX_OBJECTS 100

typedef struct {
    float x1, y1, x2, y2;
    float confidence;
    int class_id;
    int track_id;
    char class_name[32];
} Detection;

typedef struct {
    uint8_t* data;
    int width;
    int height;
    int channels;
    int64_t timestamp;
    int camera_id;
} Frame;

typedef struct {
    char rtsp_url[MAX_RTSP_URL_LEN];
    char username[64];
    char password[64];
    int width;
    int height;
    int fps;
    bool enabled;
} CameraConfig;

typedef struct {
    float iou_threshold;
    float confidence_threshold;
    int max_detections;
    int nms_enabled;
} DetectionParams;

typedef struct {
    void (*on_detection)(Detection* det, int count, Frame* frame);
    void (*on_face_detected)(char* name, float confidence, Frame* frame);
    void (*on_plate_detected)(char* plate, float confidence, Frame* frame);
    void (*on_alert)(char* message, int severity);
} CallbackFunctions;

#endif
