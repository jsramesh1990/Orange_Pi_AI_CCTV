// src/c/motion_detection.c
#include "motion_detection.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

typedef struct {
    uint8_t* prev_frame;
    int width;
    int height;
    float threshold;
    int min_area;
    int* motion_map;
} MotionDetector;

MotionDetector* motion_init(int width, int height, float threshold, int min_area) {
    MotionDetector* md = (MotionDetector*)calloc(1, sizeof(MotionDetector));
    md->width = width;
    md->height = height;
    md->threshold = threshold;
    md->min_area = min_area;
    md->prev_frame = (uint8_t*)malloc(width * height);
    md->motion_map = (int*)calloc(width * height, sizeof(int));
    return md;
}

int motion_detect(MotionDetector* md, Frame* frame, Detection* detections) {
    if (!md->prev_frame) {
        for (int i = 0; i < md->width * md->height; i++) {
            md->prev_frame[i] = frame->data[i * 3];
        }
        return 0;
    }
    
    int motion_count = 0;
    int* motion_map = md->motion_map;
    memset(motion_map, 0, md->width * md->height * sizeof(int));
    
    // Calculate frame difference
    for (int y = 1; y < md->height - 1; y++) {
        for (int x = 1; x < md->width - 1; x++) {
            int idx = y * md->width + x;
            int curr_gray = frame->data[idx * 3];
            int prev_gray = md->prev_frame[idx];
            int diff = abs(curr_gray - prev_gray);
            
            if (diff > md->threshold) {
                motion_map[idx] = 1;
                motion_count++;
                md->prev_frame[idx] = curr_gray;
            }
        }
    }
    
    // Find connected components (simple flood fill for motion areas)
    int visited[MAX_FRAME_SIZE] = {0};
    int detection_idx = 0;
    
    for (int y = 0; y < md->height && detection_idx < MAX_OBJECTS; y++) {
        for (int x = 0; x < md->width; x++) {
            int idx = y * md->width + x;
            if (motion_map[idx] && !visited[idx]) {
                // Flood fill to get bounding box
                int min_x = x, max_x = x;
                int min_y = y, max_y = y;
                int stack[4096];
                int stack_ptr = 0;
                stack[stack_ptr++] = idx;
                visited[idx] = 1;
                
                while (stack_ptr > 0) {
                    int current = stack[--stack_ptr];
                    int cx = current % md->width;
                    int cy = current / md->width;
                    
                    min_x = (cx < min_x) ? cx : min_x;
                    max_x = (cx > max_x) ? cx : max_x;
                    min_y = (cy < min_y) ? cy : min_y;
                    max_y = (cy > max_y) ? cy : max_y;
                    
                    // Check 4 neighbors
                    for (int dy = -1; dy <= 1; dy++) {
                        for (int dx = -1; dx <= 1; dx++) {
                            if (dx == 0 && dy == 0) continue;
                            int nx = cx + dx;
                            int ny = cy + dy;
                            if (nx >= 0 && nx < md->width && ny >= 0 && ny < md->height) {
                                int nidx = ny * md->width + nx;
                                if (motion_map[nidx] && !visited[nidx]) {
                                    visited[nidx] = 1;
                                    stack[stack_ptr++] = nidx;
                                }
                            }
                        }
                    }
                }
                
                int area = (max_x - min_x) * (max_y - min_y);
                if (area > md->min_area) {
                    detections[detection_idx].x1 = min_x;
                    detections[detection_idx].y1 = min_y;
                    detections[detection_idx].x2 = max_x;
                    detections[detection_idx].y2 = max_y;
                    detections[detection_idx].confidence = 1.0;
                    detections[detection_idx].class_id = -1;
                    strcpy(detections[detection_idx].class_name, "motion");
                    detection_idx++;
                }
            }
        }
    }
    
    return detection_idx;
}

void motion_destroy(MotionDetector* md) {
    if (md) {
        free(md->prev_frame);
        free(md->motion_map);
        free(md);
    }
}
