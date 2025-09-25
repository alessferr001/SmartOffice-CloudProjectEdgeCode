# Smart Office Monitoring System

In modern office environments, ensuring comfort, productivity, and energy efficiency has become highly relevant. Traditional static setups fail to adapt to dynamic situations such as fluctuating temperatures, ambient light, and long periods of inactivity.

To alleviate these challenges, this project proposes a **Smart Office Monitoring System** that leverages **IoT devices**, **Edge Computing**, and **Cloud Computing** (using AWS) to create a dynamic and intelligent office environment.

The system continuously monitors three key environmental and behavioral parameters:

* **Luminosity**
* **Temperature**
* **Human activity**

These are sensed using dedicated sensors connected tothe **edge node**.

## Human Activity Recognition

A major functionality of the system is **real-time human activity recognition** using wearable sensors. The edge device performs local classification of user behavior such as:

* Sitting
* Walking
* Standing
* Running

This capability enables the system to detect unhealthy patterns (e.g., prolonged sitting) and trigger context-aware actions or alerts.

## Edge and Cloud Architecture

* The **Edge device** preprocesses sensor data and executes immediate actions (e.g., turn on fan or lights based on thresholds), ensuring timely responses.
* Processed data is sent to the **Cloud** for storage, visualization, and advanced analysis, enabling energy usage reports and proactive notifications.
* By combining **local responsiveness** through Edge Computing and **data persistence** in the Cloud, the system provides an **efficient, scalable, and cost-effective solution** to improve working conditions and automate environment control.

## Sensors and Devices

The system integrates environmental and behavioral sensing using two main sensor types:

* **TelosB motes** – measuring temperature and luminosity
* **Shimmer2R wearable sensors** – capturing accelerometer data for activity recognition

**Edge platform:**

**Software:** Python scripts for:

* Local data collection
* Threshold-based control rules
* Real-time user activity detection

Immediate actions such as switching lights or adjusting fans are performed **locally** for responsiveness.

## Data Flow and Cloud Integration

1. Sensor data from the Edge is sent to a locally hosted **Node-RED instance**, enabling:

   * Easy management of sensor connections via a visual dashboard
   * Flexible data routing and formatting

2. Data is transmitted via **MQTT protocol (secured with TLS)** and routed through **AWS IoT Core**, which acts as a broker.

3. On an **AWS EC2 instance**, Node-RED handles ingestion and preprocessing, then forwards data to a **local InfluxDB database** for persistent time-series storage.

4. **AWS Grafana** is connected to InfluxDB to visualize environmental sensor metrics and user activity data in real time across multiple dashboards.

5. **AWS Lambda** generates periodic reports summarizing:

   * Energy consumption
   * User activities
   * Environmental conditions

6. **Grafana Alerting** combined with **Amazon SNS** notifies users in cases of prolonged sitting or abnormal environmental readings.

## System Diagram

![Smart Office System](https://github.com/user-attachments/assets/50c4eac5-38bf-42d7-8844-f78c8b8e3653)

## Edge Device Codebase

The Python code executed constitutes the **logical core of the Edge system**, performing two main functions:

1. **Real-time response** (activity recognition and environmental actuation)
2. **Preprocessing data** before forwarding to the Cloud

### 1. Activity Recognition System

* **Input:** Raw data from Shimmer2R wearable sensors

* **ML Technique:** K-Nearest Neighbors (KNN)

* **Signal Processing:** Data is segmented into temporal windows

* **Feature Extraction:**

  * Mean
  * Variance
  * Standard Deviation
  * Maximum and Minimum
  * Absolute value of the sum of the first derivative's calculated values

* **Output:** Predicted current activity (e.g., sitting, walking)

### 2. Environmental Management System

* **Sensor Data Reading:** Temperature and Luminosity values from TelosB sensors via serial port

```
def readFromSensor(serial_port):
    # Decode and parse sensor data from the serial line
    ...
```

* **Actuation Logic (Threshold-Based Control):**

  * **Temperature:** Activate actuator if temperature is outside ideal range
  * **Luminosity:** Activate lighting if brightness is too high or low
* **Actuation Time:** Recorded for energy cost calculation

### 3. Data Transmission Flow

* Processed data (activity classification and actuation time) is sent to **local Node-RED**
* Data transfer uses **persistent TCP connections** on dedicated ports
* Node-RED publishes data to **AWS IoT Core** via **MQTT over TLS**



## AWS Grafana Dashboards

To provide real-time visualization of environmental and behavioral data, **AWS Grafana** is used as the system's main monitoring dashboard. It is connected directly to the InfluxDB database hosted on the EC2 instance and visualizes the sensor and actuator data received, including:

* Temperature
* Luminosity
* User Activity
* Fan and Light Activation costs

The dashboard offers time-series graphs for temperature and luminosity trends, and pie charts to summarize user activity proportions during a given period.

<img width="853" height="618" alt="Screenshot 2025-09-25 123936" src="https://github.com/user-attachments/assets/6e2b09b1-fe02-4a13-97d6-6c8be6f2666f" />

<img width="757" height="198" alt="Screenshot 2025-09-25 124008" src="https://github.com/user-attachments/assets/989d6a4b-d5b5-4ca7-a5ab-02b67243db3b" />

## Grafana Alerting and Notifications

Moreover, the **Grafana Alerting Engine** is configured to trigger notifications via **AWS SNS** when abnormal situations are detected, such as:

* Prolonged Sitting Time
* Excessive Temperature Levels

These alerts are sent via email to notify users in real time for safety and responsiveness.

<img width="536" height="496" alt="Screenshot 2025-09-25 124124" src="https://github.com/user-attachments/assets/050dae47-cd41-4d58-a2e5-822ee2786bd5" />




