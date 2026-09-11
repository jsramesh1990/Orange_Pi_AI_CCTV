// src/cpp/deepsort.cpp
#include "deepsort.h"
#include <cmath>
#include <algorithm>
#include <cstring>
#include <cstdlib>

// KalmanFilter implementation
KalmanFilter::KalmanFilter() {
    // Initialize matrices (7-state Kalman filter)
    F = new float[49](); // 7x7 identity
    H = new float[28](); // 4x7 measurement matrix
    R = new float[16](); // 4x4 measurement noise
    Q = new float[49](); // 7x7 process noise
    P = new float[49](); // 7x7 covariance
    x = new float[7]();  // 7-state vector
    
    // Set identity for F
    for (int i = 0; i < 7; i++) F[i * 7 + i] = 1.0f;
    
    // H matrix: [1 0 0 0 0 0 0; 0 1 0 0 0 0 0; 0 0 1 0 0 0 0; 0 0 0 1 0 0 0]
    H[0] = H[8] = H[16] = H[24] = 1.0f;
    
    // R matrix (measurement noise)
    for (int i = 0; i < 4; i++) R[i * 4 + i] = 4.0f;
    
    // Q matrix (process noise)
    for (int i = 0; i < 7; i++) Q[i * 7 + i] = 0.1f;
    
    // P matrix (initial covariance)
    for (int i = 0; i < 7; i++) P[i * 7 + i] = 100.0f;
}

KalmanFilter::~KalmanFilter() {
    delete[] F; delete[] H; delete[] R; delete[] Q; delete[] P; delete[] x;
}

void KalmanFilter::predict() {
    // x = F * x
    float new_x[7] = {0};
    for (int i = 0; i < 7; i++) {
        for (int j = 0; j < 7; j++) {
            new_x[i] += F[i * 7 + j] * x[j];
        }
    }
    memcpy(x, new_x, sizeof(float) * 7);
    
    // P = F * P * F^T + Q
    float FP[49] = {0};
    for (int i = 0; i < 7; i++) {
        for (int j = 0; j < 7; j++) {
            for (int k = 0; k < 7; k++) {
                FP[i * 7 + j] += F[i * 7 + k] * P[k * 7 + j];
            }
        }
    }
    
    float new_P[49] = {0};
    for (int i = 0; i < 7; i++) {
        for (int j = 0; j < 7; j++) {
            for (int k = 0; k < 7; k++) {
                new_P[i * 7 + j] += FP[i * 7 + k] * F[j * 7 + k];
            }
        }
    }
    
    for (int i = 0; i < 49; i++) P[i] = new_P[i] + Q[i];
}

void KalmanFilter::update(float* measurement) {
    // K = P * H^T * (H * P * H^T + R)^-1
    float PHt[28] = {0};
    for (int i = 0; i < 7; i++) {
        for (int j = 0; j < 4; j++) {
            for (int k = 0; k < 7; k++) {
                PHt[i * 4 + j] += P[i * 7 + k] * H[j * 7 + k];
            }
        }
    }
    
    float HPHt[16] = {0};
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) {
            for (int k = 0; k < 7; k++) {
                HPHt[i * 4 + j] += H[i * 7 + k] * PHt[k * 4 + j];
            }
        }
    }
    
    // Add R
    for (int i = 0; i < 16; i++) HPHt[i] += R[i];
    
    // Simplified inverse for 4x4 matrix
    float inv[16];
    // ... matrix inversion (simplified for brevity)
    float S_inv[16];
    memcpy(S_inv, HPHt, sizeof(float) * 16);
    
    float K[28] = {0};
    for (int i = 0; i < 7; i++) {
        for (int j = 0; j < 4; j++) {
            for (int k = 0; k < 4; k++) {
                K[i * 4 + j] += PHt[i * 4 + k] * S_inv[k * 4 + j];
            }
        }
    }
    
    // y = z - H*x
    float y[4];
    for (int i = 0; i < 4; i++) {
        y[i] = measurement[i];
        for (int j = 0; j < 7; j++) {
            y[i] -= H[i * 7 + j] * x[j];
        }
    }
    
    // x = x + K*y
    float new_x[7];
    memcpy(new_x, x, sizeof(float) * 7);
    for (int i = 0; i < 7; i++) {
        for (int j = 0; j < 4; j++) {
            new_x[i] += K[i * 4 + j] * y[j];
        }
    }
    memcpy(x, new_x, sizeof(float) * 7);
    
    // P = (I - K*H) * P
    float I_KH[49] = {0};
    for (int i = 0; i < 7; i++) I_KH[i * 7 + i] = 1.0f;
    
    for (int i = 0; i < 7; i++) {
        for (int j = 0; j < 7; j++) {
            for (int k = 0; k < 4; k++) {
                I_KH[i * 7 + j] -= K[i * 4 + k] * H[k * 7 + j];
            }
        }
    }
    
    float new_P[49] = {0};
    for (int i = 0; i < 7; i++) {
        for (int j = 0; j < 7; j++) {
            for (int k = 0; k < 7; k++) {
                new_P[i * 7 + j] += I_KH[i * 7 + k] * P[k * 7 + j];
            }
        }
    }
    memcpy(P, new_P, sizeof(float) * 49);
}

float* KalmanFilter::get_state() {
    return x;
}

// Track implementation
Track::Track(int id, float* bbox) : track_id(id), hits(1), no_losses(0), age(0), confirmed(false) {
    kf = new KalmanFilter();
    last_bbox = new float[4];
    memcpy(last_bbox, bbox, sizeof(float) * 4);
    
    float measurement[4] = {
        (bbox[0] + bbox[2]) / 2,
        (bbox[1] + bbox[3]) / 2,
        (bbox[2] - bbox[0]),
        (bbox[3] - bbox[1])
    };
    
    float* state = kf->get_state();
    for (int i = 0; i < 4; i++) state[i] = measurement[i];
}

Track::~Track() {
    delete kf;
    delete[] last_bbox;
}

void Track::predict() {
    kf->predict();
    age++;
}

void Track::update(float* bbox, std::vector<float>& feature) {
    float measurement[4] = {
        (bbox[0] + bbox[2]) / 2,
        (bbox[1] + bbox[3]) / 2,
        (bbox[2] - bbox[0]),
        (bbox[3] - bbox[1])
    };
    kf->update(measurement);
    memcpy(last_bbox, bbox, sizeof(float) * 4);
    features = feature;
    hits++;
    no_losses = 0;
    
    if (hits >= 3) confirmed = true;
}

bool Track::is_dead() {
    return no_losses > 30;
}

// DeepSORT implementation
DeepSORT::DeepSORT(int max_age, int min_hits, float iou_threshold) 
    : next_id(0), max_age(max_age), min_hits(min_hits), iou_threshold(iou_threshold) {}

DeepSORT::~DeepSORT() {
    for (auto& pair : tracks) {
        delete pair.second;
    }
}

float DeepSORT::calculate_iou(float* bbox1, float* bbox2) {
    float x1 = std::max(bbox1[0], bbox2[0]);
    float y1 = std::max(bbox1[1], bbox2[1]);
    float x2 = std::min(bbox1[2], bbox2[2]);
    float y2 = std::min(bbox1[3], bbox2[3]);
    
    if (x2 < x1 || y2 < y1) return 0.0f;
    
    float intersection = (x2 - x1) * (y2 - y1);
    float area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1]);
    float area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1]);
    float union_area = area1 + area2 - intersection;
    
    return intersection / union_area;
}

std::vector<Track*> DeepSORT::update(Detection* detections, int count, Frame* frame) {
    std::vector<Track*> active_tracks;
    
    if (count == 0) {
        for (auto it = tracks.begin(); it != tracks.end();) {
            it->second->no_losses++;
            if (it->second->is_dead()) {
                delete it->second;
                it = tracks.erase(it);
            } else {
                it->second->predict();
                active_tracks.push_back(it->second);
                ++it;
            }
        }
        return active_tracks;
    }
    
    // Build cost matrix based on IOU
    std::vector<std::vector<float>> cost_matrix;
    std::vector<int> track_indices;
    
    for (auto& pair : tracks) {
        track_indices.push_back(pair.first);
        std::vector<float> row;
        for (int i = 0; i < count; i++) {
            float iou = calculate_iou(pair.second->last_bbox, detections[i].bbox);
            row.push_back(1.0f - iou);
        }
        cost_matrix.push_back(row);
    }
    
    // Hungarian algorithm for assignment
    std::vector<int> assignment;
    hungarian_algorithm(cost_matrix, assignment);
    
    std::vector<bool> matched_detections(count, false);
    std::vector<bool> matched_tracks(tracks.size(), false);
    
    // Update matched tracks
    for (size_t i = 0; i < assignment.size(); i++) {
        if (assignment[i] >= 0 && cost_matrix[i][assignment[i]] < 0.7f) {
            int track_id = track_indices[i];
            tracks[track_id]->update(detections[assignment[i]].bbox, 
                extract_features(frame, detections[assignment[i]].bbox));
            active_tracks.push_back(tracks[track_id]);
            matched_tracks[i] = true;
            matched_detections[assignment[i]] = true;
        }
    }
    
    // Create new tracks for unmatched detections
    for (int i = 0; i < count; i++) {
        if (!matched_detections[i]) {
            Track* new_track = new Track(next_id++, detections[i].bbox);
            tracks[new_track->track_id] = new_track;
            active_tracks.push_back(new_track);
        }
    }
    
    // Update unmatched tracks
    for (size_t i = 0; i < track_indices.size(); i++) {
        if (!matched_tracks[i]) {
            tracks[track_indices[i]]->no_losses++;
            tracks[track_indices[i]]->predict();
            if (!tracks[track_indices[i]]->is_dead()) {
                active_tracks.push_back(tracks[track_indices[i]]);
            } else {
                delete tracks[track_indices[i]];
                tracks.erase(track_indices[i]);
            }
        }
    }
    
    return active_tracks;
}

std::vector<float> DeepSORT::extract_features(Frame* frame, float* bbox) {
    std::vector<float> features(128, 0.0f);
    // Simplified feature extraction
    // In production, use a proper feature extractor (e.g., ResNet)
    return features;
}

void DeepSORT::hungarian_algorithm(std::vector<std::vector<float>>& cost_matrix, 
                                   std::vector<int>& assignment) {
    // Simplified Hungarian algorithm implementation
    // For production, use a proper implementation
    assignment.assign(cost_matrix.size(), -1);
    std::vector<bool> assigned_col(cost_matrix[0].size(), false);
    
    for (size_t i = 0; i < cost_matrix.size(); i++) {
        int best_col = -1;
        float best_cost = 1e9;
        
        for (size_t j = 0; j < cost_matrix[i].size(); j++) {
            if (!assigned_col[j] && cost_matrix[i][j] < best_cost) {
                best_cost = cost_matrix[i][j];
                best_col = j;
            }
        }
        
        if (best_col >= 0) {
            assignment[i] = best_col;
            assigned_col[best_col] = true;
        }
    }
}
