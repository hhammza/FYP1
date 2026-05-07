@echo off
title AMRPredict — Training Models
color 0B

echo.
echo  ============================================
echo   AMRPredict — Model Training
echo  ============================================
echo.
echo  This will train:
echo    1. LightGBM AMR Forecasting (~3 min)
echo    2. K-mer Resistance Predictor (~5 min)
echo.
echo  Press any key to start training, or Ctrl+C to cancel...
pause >nul

cd /d "%~dp0backend"

echo.
echo [Training] Starting model training...
python train_models.py --model all

echo.
echo  ============================================
echo   Training Complete!
echo  ============================================
echo.
echo  Models saved to: backend\trained_models\
echo.
pause
