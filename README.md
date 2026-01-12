# Student Affairs Integrated Intelligent Management System  
# 学生日常事务一体化智能管理系统

---
### 📌 项目简介

本项目是针对高校学生管理场景开发的“全流程线上管理系统”。通过集成地理围栏、智能核验及自动化流转技术，实现了请假销假、晚归查寝、考勤统计等事务的规范化与高效化。

### ✨ 核心功能

- 全流程请销假： 学生在线申请，辅导员移动端一键审批，支持销假码验证。

- 智能查寝打卡： 基于 LBS 地理围栏技术，自动校验学生打卡位置，防止异地代打。

- 异常自动预警： 后端自动扫描异常晚归、未请假离校等行为，实时推送至辅导员端。

- 可视化数据看板： 一键生成考勤报表，支持 Excel/PDF 导出，数据分析一目了然。

### 🛠 技术栈

后端 (Backend): Django 4.2 + Django Rest Framework (DRF)

前端 (Frontend): Vue 3 + Element Plus + Axios

数据库 (Database): MySQL 8.0 + Redis (缓存与地理位置计算)

任务调度: Celery / Django-Q (处理异常自动预警)

---
### 📌 Project Overview

An all-in-one digital management system designed for university student affairs. It streamlines daily routines such as leave requests, dormitory attendance, and statistical reporting through an automated and intelligent workflow.

### ✨ Key Features

- End-to-End Leave Management: Digital submission, multi-level approval workflow, and verification-based check-in.

- Smart Attendance (LBS): Utilizes Geo-fencing technology to verify student locations during dormitory checks, preventing fraudulent check-ins.

- Automated Anomaly Alerts: Backend services monitor late returns or unauthorized absences, sending real-time alerts to counselors.

- Data Analytics Dashboard: Generates comprehensive attendance reports with one-click export to Excel/PDF.

### 🛠 Tech Stack

Backend: Django 4.2 + Django Rest Framework (DRF)

Frontend: Vue 3 + Element Plus + Axios

Database: MySQL 8.0 + Redis (Cache & Geo-spatial queries)

Task Scheduling: Celery / Django-Q for automated alert processing.

## 🚀 Quick Start / 快速启动
1. Backend Setup / 后端配置

```Bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
2. Frontend Setup / 前端配置

```Bash
cd frontend
npm install
npm run dev
```
## 📸 System Preview / 系统预览

Dashboard - Attendance statistics overview.

Leave Process - The workflow of application and approval.

Map Check-in - Visual representation of Geo-fencing.

## 📧 Contact / 联系方式  
Author: [Your Name/Team Name]

Project Link: [Link to Repository]