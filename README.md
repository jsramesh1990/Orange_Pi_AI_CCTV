# 📈 Stock Analyzer - C-Based Stock Market Data Analysis Tool

![C Language](https://img.shields.io/badge/language-C-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)
![Version](https://img.shields.io/badge/version-1.0.0-brightgreen)
![Build Status](https://img.shields.io/badge/build-passing-success)

## 📋 Description
The Stock Analyzer is a C-based program designed to process and analyze stock market data efficiently from text files. It reads structured stock data, computes key insights such as price trends, averages, highs, and lows, and displays them in a formatted table for quick evaluation.

**Key Demonstrations:**
- File handling and data parsing in C
- Data structure usage for record management
- Modular programming (multiple .c files)
- Command-line based report generation

## 📁 Files Overview
stock_analyzer.c → Main program logic for stock analysis
stock_2.c → Alternate or extended analysis functions
table.c → Handles formatted data display
analyze_stock.c → Supporting or experimental analysis module
stock_data.txt → Sample dataset for analysis
README.md → Project documentation

## ✨ Features
| Feature | Description |
|---------|-------------|
| 📊 Data Parsing | Reads structured stock data from text files |
| 📈 Trend Analysis | Computes price trends and patterns |
| 📉 Statistics | Calculates averages, highs, lows, and volatility |
| 🖥️ Formatted Output | Displays results in clean tables |
| 🔧 Modular Design | Separate modules for analysis and display |
| ⚡ Performance | Optimized C for rapid processing |

## 🚀 Quick Start

### Prerequisites
- GCC compiler (version 4.8 or higher)
- Unix/Linux environment (or Windows with MinGW)

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/stock-analyzer.git
cd stock-analyzer

# Compile the program
gcc stock_analyzer.c -o stock_analyzer

# Run the analyzer
./stock_analyzer

# With debugging symbols
gcc -g stock_analyzer.c -o stock_analyzer_debug

# Multi-file compilation
gcc stock_analyzer.c table.c stock_2.c -o stock_analyzer_full

# With optimization
gcc -Wall -Wextra -O2 stock_analyzer.c -o stock_analyzer_opt

╔══════════════════════════════════════════════════════════════╗
║                    STOCK MARKET ANALYSIS                     ║
╠══════════╦══════════╦══════════╦══════════╦══════════════════╣
║ Ticker   ║   High   ║   Low    ║   Avg    ║     Trend        ║
╠══════════╬══════════╬══════════╬══════════╬══════════════════╣
║ AAPL     ║ 175.42   ║ 170.23   ║ 172.84   ║   ▲ +2.3%        ║
║ GOOGL    ║ 142.67   ║ 138.91   ║ 140.55   ║   ▼ -1.2%        ║
║ MSFT     ║ 378.15   ║ 372.48   ║ 375.32   ║   ▲ +0.8%        ║
║ AMZN     ║ 158.92   ║ 154.12   ║ 156.78   ║   ▲ +1.5%        ║
║ TSLA     ║ 222.30   ║ 215.67   ║ 218.99   ║   ▼ -0.4%        ║
╚══════════╩══════════╩══════════╩══════════╩══════════════════╝

SUMMARY STATISTICS:
═══════════════════════════════════════════════════════════════
Records: 5 | Avg Close: $212.90 | High: $378.15 (MSFT) | Low: $138.91 (GOOGL)
Bullish: 3 | Bearish: 2


