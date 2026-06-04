// include/config.h
#ifndef CONFIG_H
#define CONFIG_H

#include "common.h"

typedef struct {
    char db_host[256];
    int db_port;
    char db_user[64];
    char db_password[128];
    char db_name[64];
    
    char redis_host[256];
    int redis_port;
    char redis_password[128];
    
    char mqtt_broker[256];
    int mqtt_port;
    char mqtt_user[64];
    char mqtt_password[128];
    
    char telegram_token[512];
    char telegram_chat_id[64];
    
    CameraConfig cameras[MAX_CAMERAS];
    int camera_count;
    
    DetectionParams detection_params;
    
    int use_npu;
    int use_gpu;
    int threads;
    char model_path[512];
    char face_model_path[512];
} AppConfig;

AppConfig* load_config(const char* config_file);
void free_config(AppConfig* config);

#endif
