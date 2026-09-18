Project Statement - JutsuCam

1. Problem Statement

Real-time vision-based gesture recognition often struggles on consumer hardware due to high computational overhead, sensitivity to user distance and varying camera perspectives, and sluggish response times. Traditional pixel-level deep learning classifiers require continuous, resource-heavy convolutional processing that degrades framerates on everyday machines. JutsuCam solves this challenge by delivering a lightweight, low-latency, real-time computer vision system that extracts 3D skeletal landmarks, normalizes joint topology to achieve scale and translation invariance, and rapidly classifies complex multi-finger hand formations ("jutsus") to trigger interactive visual effects and HUD overlays at 30+ frames per second.

2. Scope of the Project

In-Scope:

Live video ingestion and frame preprocessing via OpenCV.

Multi-point hand landmark tracking using Google MediaPipe Hands (21 keypoints per hand).

Normalization of hand landmark vectors relative to the wrist origin and hand bounding scale.

Geometric and angular feature extraction for rule-based and spatial gesture classification.

Temporal smoothing and debouncing buffers to eliminate detection flicker.

Real-time compositing of interactive HUD feedback, dynamic effects, and tracking meshes directly onto the video feed.

Out-of-Scope:

Full-body skeletal kinematics or multi-person full pose estimation.

Heavy cloud-based neural network model streaming.

Complex 3D volumetric mesh rendering requiring dedicated discrete GPU hardware.

Speech, acoustic, or multimodal gesture synthesis.

3. Target Users

Creative Technologists & Content Streamers: Creators looking to trigger customized visual effects and dynamic overlays using natural hand gestures during live broadcasts.

Human-Computer Interaction (HCI) Researchers & Students: Practitioners studying real-time interaction pipelines, landmark feature engineering, and edge-deployable computer vision interfaces.

Gamers & Interactive Enthusiasts: Users who want immersive, touch-free gesture input for interactive software and gaming mechanisms.

4. High-Level Features

Real-Time Landmark Ingestion: Captures high-framerate video feeds and extracts 21 three-dimensional hand joints with sub-millisecond per-frame feature formatting.

Scale-Invariant Geometric Classifier: Evaluates relative joint distances, angles, and directional vectors to reliably identify complex multi-finger seals regardless of distance from the camera.

Temporal Debouncing Engine: Implements a sliding-window frame verification queue to prevent false-positive triggers during transitional hand movements.

Interactive Visual Overlay Engine: Automatically composites dynamic particle effects, HUD bounding indicators, and visual responses onto the camera feed upon confirmed gesture detection.
