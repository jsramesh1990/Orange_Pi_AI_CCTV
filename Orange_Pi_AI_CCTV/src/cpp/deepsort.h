// src/cpp/deepsort.h
#ifndef DEEPSORT_H
#define DEEPSORT_H

#include "../../include/common.h"
#include <vector>
#include <map>

class KalmanFilter {
private:
    float* F; // State transition matrix
    float* H; // Measurement matrix
    float* R; // Measurement noise
    float* Q; // Process noise
    float* P; // Covariance matrix
    float* x; // State vector [cx, cy, s, r, vx, vy, vs]
    
public:
    KalmanFilter();
    ~KalmanFilter();
    void predict();
    void update(float* measurement);
    float* get_state();
};

class Track {
public:
    int track_id;
    KalmanFilter* kf;
    std::vector<float> features;
    int hits;
    int no_losses;
    int age;
    float* last_bbox;
    bool confirmed;
    
    Track(int id, float* bbox);
    ~Track();
    void predict();
    void update(float* bbox, std::vector<float>& feature);
    bool is_dead();
};

class DeepSORT {
private:
    std::map<int, Track*> tracks;
    int next_id;
    int max_age;
    int min_hits;
    float iou_threshold;
    float feature_threshold;
    
    float calculate_iou(float* bbox1, float* bbox2);
    std::vector<float> extract_features(Frame* frame, float* bbox);
    void hungarian_algorithm(std::vector<std::vector<float>>& cost_matrix, 
                             std::vector<int>& assignment);
    
public:
    DeepSORT(int max_age = 30, int min_hits = 3, float iou_threshold = 0.3);
    ~DeepSORT();
    std::vector<Track*> update(Detection* detections, int count, Frame* frame);
};

#endif
