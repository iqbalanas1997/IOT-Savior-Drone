import time

confirmation = 'no'
while confirmation != 'yes':
    # these will require limits
    dropHeight = input('What height would you like the seeds to be dropped from? (metres): ')
    dropSpacing = input('How far away do you want the drop locations to be from one another? (metres): ')
    dropColumns = input('How many columns of seeds?: ')
    dropRows = input('How many rows of seeds?: ')
    dropAreaLength = dropSpacing * (dropRows - 1)
    dropAreaWidth = dropSpacing * (dropColumns - 1)
    confirmation = raw_input('This gives you a total drop area length of %dm and a drop area width of %dm. If this is okay type "yes": ' % (dropAreaLength, dropAreaWidth) )

print('Taking off to specified drop height of %d metres..' % dropHeight)
time.sleep(dropHeight) # pause the program for 3 seconds
print('Reached target altitude')

for column in range(1, dropColumns+1): # range does not include last value, so +1

    for row in range(1, dropRows+1): # range does not include last value, so +1
        
        print('Column: %d, Row: %d' % (column, row)) # print what column and row currently at

        print('Dropping seeds.') # drop seeds
        time.sleep(3)

        print('-----')

        if column % 2 == 0 and row != dropRows: # if column number is even move relative south 
            print('Moving %dm south relative to start position.' % dropSpacing)
            time.sleep(dropSpacing)
            print('-----')
        elif row != dropRows: # if column number is odd move relative north
            print('Moving %dm north relative to start position.' % dropSpacing)
            time.sleep(dropSpacing)
            print('-----')
        else: # this means that all rows in the column have been reached. Don't move relative north or south.
            break

    if column == dropColumns: # if all rows and columns have been reached. Return to start position.
        print('Mission complete. Returning Home.')
    else:    
        print('Moving to new column. (%dm relative east)' % dropSpacing) # if there are still new columns to visit  
        time.sleep(dropSpacing)
    
    print('----------')