import numpy as np
import pandas as pd
import datetime

## Gather the data
# Data Structure:
# DateTime - Index
# Each additional column represents a location in which rainfall data was gathered
# Each row represents an hour in which rainfall data was gathered for each location (column)
rainfallData = pd.read_excel('path/to/data.xlsx')

# Specify the index (DateTime)
rainfallData.set_index(pd.DatetimeIndex(rainfallData['DateTime']), inplace=True)

## Develop Compound Annual Precipitation Intensity Index
# @param data
# @return dictionary with the following structure: { year: apiiValue }
def compoundApii(data):
    # Gather location names (column names exclusing DateTime )
    columns = list(data.columns)
    columns.remove('DateTime')
    
    # Generate columns for ease of use
    temp = data
    temp['Year'] = data.index.year
    temp['Month'] = data.index.month
    temp['Day'] = data.index.day

    apiis = {}

    # For every unique year in the dataset
    years = list(data['Year'].unique())
    for year in years:
        # Limit data by year
        dataYear = temp.query('Year == {}'.format(year))
        
        # Pick rain months where it precipitates (Mar - Nov)
        dataMonth = dataYear[dataYear['Month'].isin([3,4,5,6,7,8,9,10,11])]
        
        # Split into day rather than hour (and sum hourly rainfall) 
        dataDay = dataMonth[columns].resample('D').sum()
        
        # Get the unique days
        uniqueDays = list(dataDay.index)

        # Calculate the average rain across columns (locations)
        dataMonth['Avg_Rn_WS'] = dataMonth[columns].mean(axis=1)

        # Calculate the intensity
        intensity = calculateDailyIntensity(dataMonth, uniqueDays)

        # Attach the daily values to the dataDay frame, and sum the entire year
        intensityDf = pd.DataFrame.from_dict(intensity, orient='index', columns=['intensity'])
        dataDay = dataDay.join(intensityDf)
        yearSum = dataDay['intensity'].sum()

        # return the apiis
        apiis[year] = yearSum

    return apiis

##
# Calculates the intensity for each day
# @param data - hourly dataframe
# @param uniqueDays - each unique day in the dataset
# @return dictionary in the format of { day: dailyIntensity }
def calculateDailyIntensity(data, uniqueDays):
    final = {}
    # for day in days
    for index in uniqueDays:
        year = index.year
        month = index.month
        day = index.day
        
        # Filter data by specific day
        filteredData = data.query('Year == {}'.format(year)).query('Month == {}'.format(month)).query('Day == {}'.format(day))
        
        # Build array containing arrays of consecutive rainfall
        arr = buildConsecutiveArray(filteredData['Avg_Rn_WS'].values)

        # Get the daily total for each day
        dailyTotal = 0
        for ar in arr:
            hr2 = (len(ar)** 2)
            inch = sum(ar)
            val = (1 + (inch / hr2))**hr2
            dailyTotal += val
        final[index] = dailyTotal

    return final

## Build arrays of consecutive rainfalls to later compute compounding values
# @param column - column of average rainfalls across the watershed
# @return multidimensional array containing an array for each consecutive rainfall
def buildConsecutiveArray(column):
    columnAr = list(column)
    ar = []
    # The last index where an array was created
    startingIndex = 0
    for i in range(len(columnAr)):
        # If we hit a breaking point
        if(columnAr[i] == 0):
            # Create an array starting at the value where the last
            temp = columnAr[startingIndex:i]
            startingIndex = i + 1
            ar.append(temp)
        # Else, move on to the next value
        else:
            if(i == len(columnAr) - 1):
                temp = columnAr[startingIndex:i + 1]
                ar.append(temp)
                break
            else:
                continue
    
    # Remove empty arrays
    final = list(filter(None, ar))

    return final