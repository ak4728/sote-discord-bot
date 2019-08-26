from minnowutils import *
# Trial amount
trial = 4.5
#tester
#getBotTime('minnowvotes',accountname=accountname,amount=trial,iteration=4,critical=1,minsBefore = 200)
# Main loop
''' 
    ! Critical value MUST always be higher than iteration * amount value
    ! Remember to change trial value.
''' 

config = pd.read_csv('config.csv')
accountname = config['accountname'][0]


# Main function
while True:
    try:
        if trial >= 4.7:
            trial = 4.5
        getBotTime('minnowvotes',amount=trial,accountname = accountname,iteration=6,critical=3,minsBefore = 1)
        trial = trial + 0.01
    except Exception as excp:
        print(excp)
        time.sleep(5)