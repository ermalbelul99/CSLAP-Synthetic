import argparse
import time
import os
from Data_to_Matrix_v5 import generate_final_output

def main():
    st = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('--INPUT_FILE', default=os.path.join('data','BERNER_ORDER_LINES_09-12.csv'))
    parser.add_argument('--NAME_OF_RUN', default=os.path.join('ConnexSetRun_0','r0'), type=str)
    parser.add_argument('--MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY', default=7, type=int)
    parser.add_argument('--MIN_FREQ', default=225, type=float)
    parser.add_argument('--MIN_FREQ_PREPROC', default=90, type=float)
    parser.add_argument('--RATIO_TO_KEEP', default=0.2, type=float)

    args = parser.parse_args()

    generate_final_output(
        INPUT_FILE=args.INPUT_FILE,
        NAME_OF_RUN=args.NAME_OF_RUN,
        MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY=args.MAXIMUM_NUMBER_OF_PRODUCT_PER_COMMUNITY,
        MIN_FREQ=args.MIN_FREQ,
        MIN_FREQ_PREPROC=args.MIN_FREQ_PREPROC,
        RATIO_TO_KEEP = args.RATIO_TO_KEEP

    )

    # Create a dict from the parsed arguments
   # data = vars(args)

    # Call your API function and pass in the arguments
    #api.api_reassign_products(data)
    et = time.time()
    compilation_time = et-st
    print('The process finished')
    print(compilation_time)
if __name__ == '__main__':
    main()
