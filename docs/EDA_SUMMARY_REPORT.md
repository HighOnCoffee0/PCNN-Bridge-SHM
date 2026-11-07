# EDA Summary Report
**Source file:** `C:\Users\Praji\Desktop\Hari\Main_interpolated.csv`

## 1. Dataset Overview
- Rows: **43200**  |  Columns: **48**
- Memory usage: **17.83 MB**
- Duplicate rows: **0**
- Total missing cells: **0** (0.0% of all cells)

No missing values detected in any column.


## 2. Numeric Column Summary
|                                       |   count |    mean |      std |     min |     25% |     50% |      75% |       max |     range |
|:--------------------------------------|--------:|--------:|---------:|--------:|--------:|--------:|---------:|----------:|----------:|
| Strain_microstrain                    |   43200 | 852.45  |  353.301 | 363.53  | 619.059 | 734.581 | 1076.1   |  4074.89  |  3711.36  |
| Deflection_mm                         |   43200 |  15.139 |    3.823 |   6.89  |  12.44  |  14.977 |   17.083 |    30.389 |    23.499 |
| Vibration_ms2                         |   43200 |   1.338 |    0.97  |   0.638 |   1     |   1.198 |    1.533 |    15.086 |    14.449 |
| Tilt_deg                              |   43200 |   0.756 |    0.142 |   0.476 |   0.667 |   0.724 |    0.833 |     1.523 |     1.047 |
| Displacement_mm                       |   43200 |  22.701 |    1.624 |  18.964 |  21.386 |  22.359 |   23.98  |    27.63  |     8.666 |
| Crack_Propagation_mm                  |   43200 |   0.015 |    0.009 |  -0.002 |   0.008 |   0.015 |    0.023 |     0.52  |     0.521 |
| Corrosion_Level_percent               |   43200 |   0.15  |    0.087 |  -0.01  |   0.075 |   0.15  |    0.225 |     0.313 |     0.323 |
| Cable_Member_Tension_kN               |   43200 | 476.095 |   91.801 | 334.045 | 396.925 | 447.696 |  557.036 |   844.862 |   510.817 |
| Bearing_Joint_Forces_kN               |   43200 | 277.011 |   45.55  | 205.758 | 237.479 | 260.857 |  318.366 |   423.91  |   218.152 |
| Fatigue_Accumulation_au               |   43200 |   0.3   |    0.173 |  -0.023 |   0.15  |   0.3   |    0.45  |     0.623 |     0.646 |
| Modal_Frequency_Hz                    |   43200 |   1.895 |    0.1   |   1.354 |   1.826 |   1.896 |    1.968 |     2.235 |     0.881 |
| Temperature_C                         |   43200 |  15     |    7.917 |  -1.069 |   8.799 |  15.006 |   21.231 |    30.98  |    32.049 |
| Humidity_percent                      |   43200 |  60.323 |   11.104 |  38.697 |  49.69  |  60.255 |   70.681 |    97.772 |    59.075 |
| Wind_Speed_ms                         |   43200 |   6.556 |    1.972 |   2.551 |   5.216 |   6.51  |    7.811 |    30.4   |    27.85  |
| Wind_Direction_deg                    |   43200 | 180.128 |   68.602 |  31.331 | 122.285 | 180.423 |  238.01  |   327.343 |   296.012 |
| Precipitation_mmh                     |   43200 |   0.273 |    3.028 |  -0.034 |  -0.005 |   0     |    0.006 |    40.004 |    40.038 |
| Water_Level_m                         |   43200 |   2.032 |    0.391 |   1.754 |   1.96  |   2.001 |    2.042 |     8.112 |     6.358 |
| Seismic_Activity_ms2                  |   43200 |   0     |    0.008 |  -0     |  -0     |   0     |    0     |     0.8   |     0.8   |
| Solar_Radiation_Wm2                   |   43200 | 384.54  |  373.397 | -42.41  |   1.35  | 446.361 |  768.134 |   939.206 |   981.616 |
| Air_Quality_Index_AQI                 |   43200 |  55.01  |   14.514 |  24.665 |  41.37  |  55.043 |   68.699 |    83.519 |    58.854 |
| Soil_Settlement_mm                    |   43200 |   0.301 |    0.19  |  -0.028 |   0.15  |   0.3   |    0.45  |     5.495 |     5.523 |
| Vehicle_Load_tons                     |   43200 |  17.961 |   10.477 |   5.883 |   8.746 |  16.373 |   29.032 |    53.414 |    47.531 |
| Traffic_Volume_vph                    |   43200 | 924.167 |  538.921 | 334.835 | 450.237 | 830.221 | 1498.59  |  2758.14  |  2423.3   |
| Pedestrian_Load_pph                   |   43200 | 143.566 |   83.573 |  64.777 |  85.478 |  96.37  |  201.608 |   413.164 |   348.387 |
| Impact_Events_g                       |   43200 |   0     |    0.027 |  -0     |  -0     |   0     |    0     |     4     |     4     |
| Dynamic_Load_Distribution_percent     |   43200 |  90.085 |    6.334 |  71.061 |  85.132 |  90.128 |   95.08  |   108.173 |    37.112 |
| Axle_Counts_pmin                      |   43200 |  50.656 |   28.965 |  16.348 |  24.996 |  42.313 |   74.211 |   105.184 |    88.836 |
| Structural_Health_Index_SHI           |   43200 |   0.816 |    0.053 |   0.292 |   0.797 |   0.823 |    0.845 |     0.908 |     0.616 |
| Anomaly_Detection_Score               |   43200 |   0.009 |    0.069 |   0     |   0     |   0     |    0     |     1     |     1     |
| Energy_Dissipation_au                 |   43200 |   0.273 |    1.263 |   0.016 |   0.102 |   0.156 |    0.256 |    22.499 |    22.483 |
| Acoustic_Emissions_levels             |   43200 |   8.265 |    5.167 |   0.311 |   3.307 |   8.541 |   13.202 |    28.085 |    27.774 |
| Visual_Analysis_Defect_Score          |   43200 |   0.004 |    0.003 |   0     |   0.002 |   0.004 |    0.006 |     0.106 |     0.106 |
| Electrical_Resistance_ohms            |   43200 |   0.282 |    0.029 |   0.222 |   0.257 |   0.282 |    0.306 |     0.349 |     0.127 |
| SHI_Predicted_24h_Ahead               |   43200 |   0.813 |    0.053 |   0.289 |   0.794 |   0.82  |    0.842 |     0.906 |     0.617 |
| SHI_Predicted_7d_Ahead                |   43200 |   0.796 |    0.053 |   0.263 |   0.777 |   0.803 |    0.826 |     0.89  |     0.628 |
| SHI_Predicted_30d_Ahead               |   43200 |   0.751 |    0.056 |   0.197 |   0.727 |   0.757 |    0.786 |     0.87  |     0.673 |
| Probability_of_Failure_PoF            |   43200 |   0.034 |    0.018 |   0.019 |   0.027 |   0.031 |    0.035 |     0.709 |     0.69  |
| Maintenance_Alert                     |   43200 |   0.006 |    0.078 |   0     |   0     |   0     |    0     |     1     |     1     |
| Simulated_Water_Flow_m3s              |   43200 | 232.688 |   50.187 | 196.986 | 223.471 | 228.637 |  233.94  |  1000     |   803.014 |
| Soil_Saturation_percent               |   43200 |  25.477 |   15.625 |   9.889 |  10.002 |  28.106 |   40.428 |    68.377 |    58.488 |
| Simulated_Slope_Displacement_mm       |   43200 |   0.764 |    0.798 |   0     |   0.375 |   0.749 |    1.124 |    63.736 |    63.736 |
| Simulated_Wind_Load_Pressure_kPa      |   43200 |   0.199 |    0.088 |   0.114 |   0.158 |   0.19  |    0.229 |     2     |     1.886 |
| Simulated_Localized_Stress_Index      |   43200 |   0.461 |    0.27  |   0.149 |   0.224 |   0.374 |    0.695 |     1     |     0.851 |
| Energy_Harvesting_Potential_W         |   43200 |   1.365 |    6.314 |   0.081 |   0.511 |   0.782 |    1.279 |   112.495 |   112.413 |
| Estimated_Repair_Cost_USD_incremental |   43200 | 309.152 | 3902.78  |   0.99  |   1.519 |   1.699 |    1.949 | 50014.2   | 50013.2   |
| Carbon_Footprint_tCO2e_incremental    |   43200 |   0.002 |    0.001 |   0.001 |   0.001 |   0.002 |    0.002 |     0.004 |     0.003 |


## 3. Categorical Column Summary
| column            |   n_unique | top_category   |   top_freq |   top_pct |
|:------------------|-----------:|:---------------|-----------:|----------:|
| Bridge_Mood_Meter |          3 | Stressed       |      33464 |     77.46 |


## 4. Strongest Correlations (Top 10 by |r|)
| col_1                       | col_2                                 |   correlation |
|:----------------------------|:--------------------------------------|--------------:|
| Energy_Dissipation_au       | Energy_Harvesting_Potential_W         |         1     |
| Water_Level_m               | Simulated_Water_Flow_m3s              |         0.999 |
| Structural_Health_Index_SHI | SHI_Predicted_24h_Ahead               |         0.998 |
| Corrosion_Level_percent     | Fatigue_Accumulation_au               |         0.997 |
| Vehicle_Load_tons           | Traffic_Volume_vph                    |         0.996 |
| Maintenance_Alert           | Estimated_Repair_Cost_USD_incremental |         0.995 |
| Crack_Propagation_mm        | Visual_Analysis_Defect_Score          |         0.995 |
| Structural_Health_Index_SHI | SHI_Predicted_7d_Ahead                |         0.993 |
| SHI_Predicted_24h_Ahead     | SHI_Predicted_7d_Ahead                |         0.993 |
| Vehicle_Load_tons           | Simulated_Localized_Stress_Index      |         0.988 |


## 5. Skewness & Kurtosis (per numeric column)
| column                                |   skewness | skew_interpretation     |   excess_kurtosis | kurtosis_interpretation                          |
|:--------------------------------------|-----------:|:------------------------|------------------:|:-------------------------------------------------|
| Strain_microstrain                    |     3.4443 | highly skewed right     |           25.923  | leptokurtic (heavier tails / more outlier-prone) |
| Deflection_mm                         |     0.5335 | moderately skewed right |            0.1236 | mesokurtic (normal-like tails)                   |
| Vibration_ms2                         |    10.3597 | highly skewed right     |          124      | leptokurtic (heavier tails / more outlier-prone) |
| Tilt_deg                              |     0.752  | moderately skewed right |            0.0092 | mesokurtic (normal-like tails)                   |
| Displacement_mm                       |     0.4336 | approximately symmetric |           -0.8448 | platykurtic (lighter tails / flatter peak)       |
| Crack_Propagation_mm                  |     7.0821 | highly skewed right     |          377.719  | leptokurtic (heavier tails / more outlier-prone) |
| Corrosion_Level_percent               |    -0      | approximately symmetric |           -1.1934 | platykurtic (lighter tails / flatter peak)       |
| Cable_Member_Tension_kN               |     0.6539 | moderately skewed right |           -0.7306 | platykurtic (lighter tails / flatter peak)       |
| Bearing_Joint_Forces_kN               |     0.5767 | moderately skewed right |           -1.0656 | platykurtic (lighter tails / flatter peak)       |
| Fatigue_Accumulation_au               |     0.0006 | approximately symmetric |           -1.1921 | platykurtic (lighter tails / flatter peak)       |
| Modal_Frequency_Hz                    |    -0.0915 | approximately symmetric |           -0.3433 | mesokurtic (normal-like tails)                   |
| Temperature_C                         |     0.0002 | approximately symmetric |           -1.0141 | platykurtic (lighter tails / flatter peak)       |
| Humidity_percent                      |     0.1345 | approximately symmetric |           -1.013  | platykurtic (lighter tails / flatter peak)       |
| Wind_Speed_ms                         |     2.9493 | highly skewed right     |           30.2503 | leptokurtic (heavier tails / more outlier-prone) |
| Wind_Direction_deg                    |    -0.0033 | approximately symmetric |           -1.1107 | platykurtic (lighter tails / flatter peak)       |
| Precipitation_mmh                     |    11.3356 | highly skewed right     |          129.542  | leptokurtic (heavier tails / more outlier-prone) |
| Water_Level_m                         |    12.5644 | highly skewed right     |          166.65   | leptokurtic (heavier tails / more outlier-prone) |
| Seismic_Activity_ms2                  |    74.5526 | highly skewed right     |         6296.59   | leptokurtic (heavier tails / more outlier-prone) |
| Solar_Radiation_Wm2                   |     0.0995 | approximately symmetric |           -1.7483 | platykurtic (lighter tails / flatter peak)       |
| Air_Quality_Index_AQI                 |    -0.0043 | approximately symmetric |           -1.3522 | platykurtic (lighter tails / flatter peak)       |
| Soil_Settlement_mm                    |     4.6491 | highly skewed right     |          125.18   | leptokurtic (heavier tails / more outlier-prone) |
| Vehicle_Load_tons                     |     0.6077 | moderately skewed right |           -1.1037 | platykurtic (lighter tails / flatter peak)       |
| Traffic_Volume_vph                    |     0.6094 | moderately skewed right |           -1.1    | platykurtic (lighter tails / flatter peak)       |
| Pedestrian_Load_pph                   |     1.2673 | highly skewed right     |            0.4894 | mesokurtic (normal-like tails)                   |
| Impact_Events_g                       |   146.959  | highly skewed right     |        21595      | leptokurtic (heavier tails / more outlier-prone) |
| Dynamic_Load_Distribution_percent     |    -0.0198 | approximately symmetric |           -0.7838 | platykurtic (lighter tails / flatter peak)       |
| Axle_Counts_pmin                      |     0.5588 | moderately skewed right |           -1.2481 | platykurtic (lighter tails / flatter peak)       |
| Structural_Health_Index_SHI           |    -2.319  | highly skewed left      |           13.4004 | leptokurtic (heavier tails / more outlier-prone) |
| Anomaly_Detection_Score               |    10.0914 | highly skewed right     |          114.592  | leptokurtic (heavier tails / more outlier-prone) |
| Energy_Dissipation_au                 |    13.7255 | highly skewed right     |          200.427  | leptokurtic (heavier tails / more outlier-prone) |
| Acoustic_Emissions_levels             |     0.0021 | approximately symmetric |           -1.6647 | platykurtic (lighter tails / flatter peak)       |
| Visual_Analysis_Defect_Score          |     2.8452 | highly skewed right     |          111.156  | leptokurtic (heavier tails / more outlier-prone) |
| Electrical_Resistance_ohms            |     0.0157 | approximately symmetric |           -1.0833 | platykurtic (lighter tails / flatter peak)       |
| SHI_Predicted_24h_Ahead               |    -2.314  | highly skewed left      |           13.3693 | leptokurtic (heavier tails / more outlier-prone) |
| SHI_Predicted_7d_Ahead                |    -2.2767 | highly skewed left      |           13.0762 | leptokurtic (heavier tails / more outlier-prone) |
| SHI_Predicted_30d_Ahead               |    -1.8973 | highly skewed left      |           10.2596 | leptokurtic (heavier tails / more outlier-prone) |
| Probability_of_Failure_PoF            |    10.4193 | highly skewed right     |          202.483  | leptokurtic (heavier tails / more outlier-prone) |
| Maintenance_Alert                     |    12.6745 | highly skewed right     |          158.643  | leptokurtic (heavier tails / more outlier-prone) |
| Simulated_Water_Flow_m3s              |    12.5627 | highly skewed right     |          166.588  | leptokurtic (heavier tails / more outlier-prone) |
| Soil_Saturation_percent               |     0.199  | approximately symmetric |           -1.6168 | platykurtic (lighter tails / flatter peak)       |
| Simulated_Slope_Displacement_mm       |    41.7486 | highly skewed right     |         2725.26   | leptokurtic (heavier tails / more outlier-prone) |
| Simulated_Wind_Load_Pressure_kPa      |    12.6157 | highly skewed right     |          222.701  | leptokurtic (heavier tails / more outlier-prone) |
| Simulated_Localized_Stress_Index      |     0.608  | moderately skewed right |           -1.1335 | platykurtic (lighter tails / flatter peak)       |
| Energy_Harvesting_Potential_W         |    13.7269 | highly skewed right     |          200.462  | leptokurtic (heavier tails / more outlier-prone) |
| Estimated_Repair_Cost_USD_incremental |    12.6379 | highly skewed right     |          157.834  | leptokurtic (heavier tails / more outlier-prone) |
| Carbon_Footprint_tCO2e_incremental    |     0.7611 | moderately skewed right |           -0.3864 | mesokurtic (normal-like tails)                   |


## 6. IQR-Based Outlier Summary
| column                                |       Q1 |        Q3 |       IQR |   lower_bound |   upper_bound |   n_outliers |   pct_outliers |   min_outlier_value |   max_outlier_value |
|:--------------------------------------|---------:|----------:|----------:|--------------:|--------------:|-------------:|---------------:|--------------------:|--------------------:|
| Strain_microstrain                    | 619.059  | 1076.1    |  457.04   |      -66.5003 |     1761.66   |          252 |           0.58 |           1762.12   |           4074.89   |
| Deflection_mm                         |  12.4401 |   17.0832 |    4.643  |        5.4756 |       24.0477 |          627 |           1.45 |             24.0484 |             30.3891 |
| Vibration_ms2                         |   0.9997 |    1.533  |    0.5333 |        0.1998 |        2.333  |          345 |           0.8  |              2.4074 |             15.0865 |
| Tilt_deg                              |   0.6674 |    0.8332 |    0.1657 |        0.4188 |        1.0818 |          735 |           1.7  |              1.0818 |              1.5227 |
| Displacement_mm                       |  21.3855 |   23.9798 |    2.5943 |       17.494  |       27.8713 |            0 |           0    |            nan      |            nan      |
| Crack_Propagation_mm                  |   0.0075 |    0.0225 |    0.015  |       -0.015  |        0.045  |            2 |           0    |              0.5059 |              0.5197 |
| Corrosion_Level_percent               |   0.0749 |    0.2248 |    0.1498 |       -0.1498 |        0.4495 |            0 |           0    |            nan      |            nan      |
| Cable_Member_Tension_kN               | 396.925  |  557.037  |  160.112  |      156.758  |      797.204  |          109 |           0.25 |            797.231  |            844.862  |
| Bearing_Joint_Forces_kN               | 237.479  |  318.366  |   80.8873 |      116.148  |      439.697  |            0 |           0    |            nan      |            nan      |
| Fatigue_Accumulation_au               |   0.1498 |    0.4502 |    0.3004 |       -0.3008 |        0.9008 |            0 |           0    |            nan      |            nan      |
| Modal_Frequency_Hz                    |   1.826  |    1.9685 |    0.1425 |        1.6122 |        2.1822 |           59 |           0.14 |              1.3538 |              2.2352 |
| Temperature_C                         |   8.7992 |   21.2313 |   12.4321 |       -9.849  |       39.8794 |            0 |           0    |            nan      |            nan      |
| Humidity_percent                      |  49.6898 |   70.6808 |   20.9909 |       18.2034 |      102.167  |            0 |           0    |            nan      |            nan      |
| Wind_Speed_ms                         |   5.2157 |    7.8114 |    2.5957 |        1.3222 |       11.705  |          120 |           0.28 |             19.8393 |             30.4001 |
| Wind_Direction_deg                    | 122.285  |  238.01   |  115.725  |      -51.3031 |      411.598  |            0 |           0    |            nan      |            nan      |
| Precipitation_mmh                     |  -0.0053 |    0.0056 |    0.0109 |       -0.0217 |        0.022  |          652 |           1.51 |             -0.0342 |             40.0039 |
| Water_Level_m                         |   1.9601 |    2.0419 |    0.0818 |        1.8375 |        2.1645 |          679 |           1.57 |              1.7543 |              8.1121 |
| Seismic_Activity_ms2                  |  -0      |    0      |    0      |       -0      |        0      |          385 |           0.89 |             -0      |              0.8    |
| Solar_Radiation_Wm2                   |   1.3505 |  768.134  |  766.783  |    -1148.82   |     1918.31   |            0 |           0    |            nan      |            nan      |
| Air_Quality_Index_AQI                 |  41.3702 |   68.6989 |   27.3287 |        0.3771 |      109.692  |            0 |           0    |            nan      |            nan      |
| Soil_Settlement_mm                    |   0.1502 |    0.4496 |    0.2994 |       -0.299  |        0.8987 |           10 |           0.02 |              5.47   |              5.4945 |
| Vehicle_Load_tons                     |   8.7463 |   29.0321 |   20.2858 |      -21.6825 |       59.4609 |            0 |           0    |            nan      |            nan      |
| Traffic_Volume_vph                    | 450.238  | 1498.59   | 1048.35   |    -1122.29   |     3071.11   |            0 |           0    |            nan      |            nan      |
| Pedestrian_Load_pph                   |  85.478  |  201.608  |  116.13   |      -88.717  |      375.803  |          837 |           1.94 |            375.881  |            413.164  |
| Impact_Events_g                       |  -0      |    0      |    0      |       -0      |        0      |          313 |           0.72 |             -0      |              4      |
| Dynamic_Load_Distribution_percent     |  85.1316 |   95.0798 |    9.9482 |       70.2092 |      110.002  |            0 |           0    |            nan      |            nan      |
| Axle_Counts_pmin                      |  24.9961 |   74.2114 |   49.2153 |      -48.8269 |      148.034  |            0 |           0    |            nan      |            nan      |
| Structural_Health_Index_SHI           |   0.7972 |    0.8454 |    0.0482 |        0.7249 |        0.9178 |         3081 |           7.13 |              0.2921 |              0.7249 |
| Anomaly_Detection_Score               |   0      |    0      |    0      |        0      |        0      |         1379 |           3.19 |              0.0002 |              1      |
| Energy_Dissipation_au                 |   0.1021 |    0.2557 |    0.1536 |       -0.1283 |        0.4861 |          407 |           0.94 |              0.4969 |             22.499  |
| Acoustic_Emissions_levels             |   3.3071 |   13.2019 |    9.8948 |      -11.5351 |       28.044  |            1 |           0    |             28.0852 |             28.0852 |
| Visual_Analysis_Defect_Score          |   0.0021 |    0.0063 |    0.0042 |       -0.0042 |        0.0126 |            2 |           0    |              0.1016 |              0.1055 |
| Electrical_Resistance_ohms            |   0.2572 |    0.3062 |    0.0491 |        0.1836 |        0.3798 |            0 |           0    |            nan      |            nan      |
| SHI_Predicted_24h_Ahead               |   0.7941 |    0.8425 |    0.0483 |        0.7217 |        0.9149 |         3086 |           7.14 |              0.2894 |              0.7217 |
| SHI_Predicted_7d_Ahead                |   0.7769 |    0.8258 |    0.049  |        0.7034 |        0.8993 |         2877 |           6.66 |              0.2627 |              0.7034 |
| SHI_Predicted_30d_Ahead               |   0.7269 |    0.7856 |    0.0587 |        0.6388 |        0.8736 |         1477 |           3.42 |              0.1974 |              0.6388 |
| Probability_of_Failure_PoF            |   0.0273 |    0.0353 |    0.008  |        0.0154 |        0.0473 |         3523 |           8.16 |              0.0473 |              0.7087 |
| Maintenance_Alert                     |   0      |    0      |    0      |        0      |        0      |          264 |           0.61 |              1      |              1      |
| Simulated_Water_Flow_m3s              | 223.471  |  233.94   |   10.4698 |      207.766  |      249.645  |          683 |           1.58 |            196.986  |           1000      |
| Soil_Saturation_percent               |  10.0021 |   40.4281 |   30.426  |      -35.6368 |       86.067  |            0 |           0    |            nan      |            nan      |
| Simulated_Slope_Displacement_mm       |   0.3752 |    1.1238 |    0.7486 |       -0.7476 |        2.2466 |           60 |           0.14 |              2.3779 |             63.7361 |
| Simulated_Wind_Load_Pressure_kPa      |   0.1576 |    0.2289 |    0.0713 |        0.0506 |        0.3358 |          120 |           0.28 |              0.9309 |              2      |
| Simulated_Localized_Stress_Index      |   0.2244 |    0.695  |    0.4706 |       -0.4815 |        1.401  |            0 |           0    |            nan      |            nan      |
| Energy_Harvesting_Potential_W         |   0.5107 |    1.279  |    0.7684 |       -0.6419 |        2.4316 |          408 |           0.94 |              2.4844 |            112.495  |
| Estimated_Repair_Cost_USD_incremental |   1.5187 |    1.9489 |    0.4302 |        0.8735 |        2.5942 |         2949 |           6.83 |              2.5944 |          50014.2    |
| Carbon_Footprint_tCO2e_incremental    |   0.0015 |    0.0022 |    0.0008 |        0.0003 |        0.0033 |           99 |           0.23 |              0.0033 |              0.0039 |

**Total outlier data points (IQR method) across all numeric columns: 25541**
Full row-level outlier details saved to `tables/iqr_outlier_row_details.csv`


## 7. t-SNE Projection
2D projection of all numeric columns (standardized, missing values median-imputed). See `plots/tsne_projection.png`.

Note: t-SNE was run on all 43200 rows as requested; this can be slow for datasets this large.


## 8. Time-Based Analysis
Detected datetime column(s): Timestamp
Trend, rolling mean, and seasonality (month / day-of-week) plots generated for each numeric column against each datetime column — see `plots/time_trend_*.png` and `plots/seasonality_*.png`.

Month-by-month skewness & kurtosis is saved to `tables/skew_kurtosis_by_time_period.csv`. Sample (first 10 rows):

| datetime_column   | period   | numeric_column          |     n |     mean |      std |   skewness |   excess_kurtosis |
|:------------------|:---------|:------------------------|------:|---------:|---------:|-----------:|------------------:|
| Timestamp         | 2023-01  | Strain_microstrain      | 43200 | 852.45   | 353.301  |     3.4443 |           25.923  |
| Timestamp         | 2023-01  | Deflection_mm           | 43200 |  15.1394 |   3.8226 |     0.5335 |            0.1236 |
| Timestamp         | 2023-01  | Vibration_ms2           | 43200 |   1.3378 |   0.9702 |    10.3597 |          124      |
| Timestamp         | 2023-01  | Tilt_deg                | 43200 |   0.7562 |   0.1422 |     0.752  |            0.0092 |
| Timestamp         | 2023-01  | Displacement_mm         | 43200 |  22.7012 |   1.6238 |     0.4336 |           -0.8448 |
| Timestamp         | 2023-01  | Crack_Propagation_mm    | 43200 |   0.015  |   0.0093 |     7.0821 |          377.719  |
| Timestamp         | 2023-01  | Corrosion_Level_percent | 43200 |   0.15   |   0.0867 |    -0      |           -1.1934 |
| Timestamp         | 2023-01  | Cable_Member_Tension_kN | 43200 | 476.095  |  91.8011 |     0.6539 |           -0.7306 |
| Timestamp         | 2023-01  | Bearing_Joint_Forces_kN | 43200 | 277.011  |  45.55   |     0.5767 |           -1.0656 |
| Timestamp         | 2023-01  | Fatigue_Accumulation_au | 43200 |   0.3    |   0.1735 |     0.0006 |           -1.1921 |

## 9. All Generated Files
- `plots/correlation_heatmap.png`
- `plots/distribution_histograms.png`
- `plots/boxplots_outliers.png`
- `plots/tsne_projection.png`
- `plots/categorical_frequencies.png` (if categorical columns exist)
- `plots/time_trend_<col>.png`, `plots/seasonality_<col>.png` (if datetime columns exist)
- `tables/*.csv` — all numeric tables backing every plot above