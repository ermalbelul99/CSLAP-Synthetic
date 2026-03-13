# Warehouse Connexity Problem - FINAL PROGRAM BERNER

## Overview
This Python program is designed to analyze order and product data, in order to identify subsets of highly correlated products. It then provides the total number of warehouse stations an order must pass through if the products on each of those subsets are positioned together in a same station. The solution approach involves three main steps: Preprocess, Process, and Postprocess, each responsible for handling different aspects of the data to achieve the desired outcome.

## Preparing your local machine 
1. Ensure you have Python installed in your device
2. Download and extract the zip file to your local machine.
3. Open command prompt and navigate to the project directory 
example Windows OS(cd C:\Users\YourName\Projects\Final_Program_BERNER\app).
4. Once you're in the correct directory, run the script in your command prompt based on your operating system:
-> Unix-like Systems (Linux/macOS):
```bash
  setup.sh
```
-> Windows OS:
 -->Command Prompt(cmd.exe):
```bash
  setup.bat
```
 --> PowerShell:
```bash
  .\setup.bat
```


## Running the Project
To run the project use the command line interface (CLI). Open your terminal or command prompt, activate the virtual environement (on windows: "CALL connexset\Scripts\activate.bat", on linux: "source connexset/bin/activate") then execute the following command:

```bash
python connexset.py --INPUT_FILE <your_input_file> --NAME_OF_RUN <your_run_name> --MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY <int_value> --MIN_FREQ <float_value> --MIN_FREQ_PREPROC <float_value> --RATIO_TO_KEEP <float_value>
```

Command Line Arguments:
--INPUT_FILE: Path to the input CSV file containing order, product, station data.
--NAME_OF_RUN: Name for this run; creates a new directory where the output files will be stored.
--MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY: Max number of products in a community.
--MIN_FREQ: Minimum frequency for a pair to appear in the dataset.
--MIN_FREQ_PREPROC: defiens the min number that a product needs to be ordered in the total data.
--RATIO_TO_KEEP: Minimum ratio for considering the relatedness between two products.

### Note
All the above arguments are customizable and the user can choose the values
Please ensure your input file is properly formatted considering that it should have the same format of data as in the default input file ('BERNER_ORDER_LINES_09-12.csv').

### Example:
python connexset.py --INPUT_FILE data/BERNER_ORDER_LINES_09-12.csv --NAME_OF_RUN Run_01\r_01 --MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY 10 --MIN_FREQ 200 --MIN_FREQ_PREPROC 100 --RATIO_TO_KEEP 0.15

### When the user has finished running the code:
To exit the virtual environment, users can simply type deactivate in the terminal or command prompt. 

## Output
The program generates output files in a new directory named after the --NAME_OF_RUN parameter. This includes:

1. Final output file with product-community assignments (sets.csv).
2. Graphs visualizing various aspects of the data and results.
3. CSV file detailing the parameters used for the run (parameters.csv).

## Project Files Description
Data_to_Matrix_v5.py: Core module containing functions for preprocessing, processing, and postprocessing the data.
connexset.py: Command Line Interface for running the program with user-defined parameters.

## Problem and Solution Approach
The task involves analyzing a CSV file with order and product information. The goal is to group correlated products into the same warehouse station to minimize station traversal.

Solution Approach:
1. Preprocess: Identify meaningful pairs of correlated products, filter pairs based on thresholds, and create a DataFrame of significant pairs.
2. Mainprocess: Form subsets of highly correlated products, ensuring each subset adheres to the maximum product limit and incorporates the highest-weighted pairs.
3. Postprocess: Refine subsets by adding strongly related products not included in the main process.




## Conclusion
The program follows a detailed methodology, described in the provided documentation, to achieve the optimization of warehouse stations based on product correlations.
