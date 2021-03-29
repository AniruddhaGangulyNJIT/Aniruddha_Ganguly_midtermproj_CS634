"""
Author : Aniruddha Ganguly (ag95@njit.edu)
Python Version : 3.8
Modules Reuired to Run the code
Please Run the below lines in your terminal if any of the following modules are missing

pip install pandas
pip install itertools

"""
import os
import numpy as np
import pandas as pd
import itertools


def read_data(location):
    """
    This function reads the data from the excel file.
    The excel file should have two tabs named below:
    1. Items
    2. Transactions
    The function reads the data without the header and assigns header to the dataframe afterwards.
    To run the program with a new set of data, please create an .xlsx file with two above mentioned tabs and please do not
    put header in the data as teh function automatically assigns header to avoid errors and naming conventions
    Returns :
    1. Pandas DataFrame (columns :["Item#","ItemName"])
    1. Pandas DataFrame (columns :  ["Transaction ID","Transaction"])
    """

    items = pd.read_excel(location, sheet_name = "Items", header=None,names = ["Item#","ItemName"])
    # print (items.columns)
    transactions = pd.read_excel(location, sheet_name = "Transactions", header=None,names = ["Transaction ID","Transaction"])
    # print (transactions.columns)
    print ("total number of distinct items : ",len(items.index))
    print ("total number of transactions : ", len(transactions.index))
    return items,transactions


def calculate_support(transaction,item):
    """
    :param transaction: Pandas DataFrame (columns :  ["Transaction ID","Transaction"]) | Source function : read_data()
    :param item: Pandas DataFrame (columns :["Item#","ItemName"]) | Source function : read_data()
    :return: Pandas DataFrame (Columns : ["ItemName", "Support"]
            Examples :           ItemName   Support
                        0            pear   0.875
                        1             fig    0.75
                        2           water   0.625
                        3          banana     0.5
                        4          orange     0.5
    """
    Total_transactions = len(transaction.index)
    item_temp = item
    item_temp["Support"] = 0.0
    item_temp.Support = item_temp.Support.astype(float)
    for i in item_temp.index:
        item_list = item_temp.ItemName[i].split(",")
        # print (len(item_list),item_list)
        supp = 0
        for j in transaction.index:
            # print (transaction.Transaction[j].split(","))
            if all(x in map(str.strip,transaction.Transaction[j].split(",")) for x in item_list):
                supp = supp + 1
        item_temp.loc[i,"Support"] = float(supp)/Total_transactions
    return item_temp.sort_values(by='Support',ascending=False).reset_index(drop=True)


def exclusion_process(items,transactions,min_support):
    """
    :param items: Pandas DataFrame (columns :["Item#","ItemName"]) | Source function : read_data()
    :param transactions: Pandas DataFrame (columns :  ["Transaction ID","Transaction"]) | Source function : read_data()
    :param min_support: Minimum Support ( Provided by the User while running )
    :return: Two Pandas DataFrame.
             1. low_freq_combi --> Combinations of Items which has Support below min_support
             2. high_frequent_combi --> Combinations of Items which has Support above min_support
    """
    k = 1
    low_freq_combi = []
    high_frequent_combi = pd.DataFrame(columns=["ItemName","Support"])
    distinct_items = list(set(items.ItemName))
    # print (distinct_items)

    while k < len(distinct_items):
        k_freq_df = pd.DataFrame(columns=["ItemName","Support"])
        k_freq_df["ItemName"] = [",".join(i) for i in itertools.combinations(list(items.ItemName), k)]
        support_df = calculate_support(transactions, k_freq_df)
        # print (support_df)
        low_freq_df = support_df[support_df.Support < min_support]
        low_freq_df = low_freq_df.reset_index()
        for lf in low_freq_df.index:
            low_freq_combi.append(low_freq_df.ItemName[lf])

        support_df = support_df[support_df.Support >= min_support]

        for s in support_df.index:
            l = len(high_frequent_combi.index)
            high_frequent_combi.loc[l, "ItemName"] = support_df.ItemName[s]
            high_frequent_combi.loc[l, "Support"] = support_df.Support[s]
        k = k+1
    return low_freq_combi,high_frequent_combi

def pruning(low_freq_combination,high_frequent_combination):
    """
    :param low_freq_combination: Pandas DataFrame ( source : exclusion_process() )
    :param high_frequent_combination: Pandas DataFrame ( source : exclusion_process() )
    :return: Pandas DataFrame returns Pruned High Frequent Combination on the basis of
            "superset of low Support items
             would also have low Support"
    """
    for i in low_freq_combination:
        i = i.split(",")
        for j in high_frequent_combination.index:
            if all(x in map(str.strip, high_frequent_combination.ItemName[j].split(",")) for x in i):
                high_frequent_combination = high_frequent_combination.drop(j)
                high_frequent_combination = high_frequent_combination.reset_index(drop=True)
    return high_frequent_combination


def calculate_confidence(A,B,support_df):
    """
    This function calculates the confidence of any given two sets with their support
                    Confidence(X,Y) = Support(X,Y)/Support(X)
    :return:
             printable_A --> Returns a string. Returns a string with '&' separator If there is multiple items
             printable_B --> Returns a string. Returns a string with '&' separator If there is multiple items
             support_ab --> Support of A,B
             confidence --> Calculated confidence
    """
    printable_A = " & ".join(str(x) for x in sorted(list(A)))
    printable_B = " & ".join(str(x) for x in sorted(list(B)))
    A_str = ",".join(str(x) for x in sorted(list(A)))
    AB_str = ",".join(str(x) for x in sorted(list(A) + list(B)))
    support_df["ItemName"] = [",".join(y for y in sorted(list(x))) for x in support_df.item_list]
    '''
    print (support_df)
    print (A_str)
    print (B_str)
    '''
    support_a = support_df[support_df.ItemName == A_str].Support.values[0]
    support_ab = support_df[support_df.ItemName == AB_str].Support.values[0]

    confidence = float(support_ab) / support_a
    return printable_A,printable_B,support_ab,confidence


def generate_association_rules(pruned_frequent_items, min_support, min_confidence, out_file_name):
    """
    :param pruned_frequent_items: Pandas DataFrame of pruned items who has support more than min_support (source : pruning())
    :return: Pandas DataFrame with all the Rules,Support and Confidence for all the possible permutations
    """
    Association_Rules = pd.DataFrame(columns=["Association_Rules","Support(%)","Confidence(%)"])
    pruned_frequent_items["item_list"] = [x.split(",") for x in pruned_frequent_items["ItemName"]]
    pruned_frequent_items["item_length"] = [len(x) for x in pruned_frequent_items["item_list"]]
    eligible_combinations = pruned_frequent_items[pruned_frequent_items.item_length > 1]
    # print (eligible_combinations)

    for i in eligible_combinations.index:
        for p in list(itertools.permutations(eligible_combinations.item_list[i])):
            for n in range(1,len(p)):
                rule_str_left,rule_str_right,support,confidence = calculate_confidence(list(p[:-n]), p[-n:], pruned_frequent_items)
                # print (rule_str_left,"-->",rule_str_right," | Support: ",support * 100,"%"," Confidence: ",confidence * 100, "%")
                Association_Rules.loc[-1] = [rule_str_left + " --> " + rule_str_right,support*100,confidence*100]
                Association_Rules.index = Association_Rules.index + 1
                Association_Rules = Association_Rules.sort_index()
    Association_Rules = Association_Rules.drop_duplicates()
    Association_Rules = Association_Rules.reset_index(drop = True)
    Association_Rules = Association_Rules.sort_index(ascending=False)
    Association_Rules = Association_Rules.reset_index(drop = True)
    Association_Rules = Association_Rules[Association_Rules["Confidence(%)"] >= min_confidence * 100]
    Association_Rules.to_csv(os.getcwd() + "/output/" + out_file_name + "_" + str(min_support * 100) + '_' + str(min_confidence * 100) + ".csv",header=True)
    return Association_Rules


def run_Apriori(items, transactions, min_support, min_cofidence, out_file_name):
    low_freq_combi, high_frequent_combi = exclusion_process(items, transactions, min_support)
    # print (high_frequent_combi)
    high_frequent_combi = pruning(low_freq_combi, high_frequent_combi)
    association_rules = generate_association_rules(high_frequent_combi, min_support, min_cofidence, out_file_name)
    print (association_rules)





if __name__ == "__main__":
    input_location = os.getcwd() + "/input/"
    all_files_available = [f for f in os.listdir(input_location) if os.path.isfile(os.path.join(input_location, f))]
    all_xlsx_inputs_available = [x for x in all_files_available if x[-5:] == '.xlsx']
    print ("\n-------------------PARAMETERS-------------------\n")
    location = input_location + str(input("Enter the Database Name from the following list \n" + ''.join(
        ['--' + x + '\n' for x in all_xlsx_inputs_available]) + "\nFile Name: "))
    min_support = float(input("Enter a minimum support value: "))
    min_confidence = float(input("Enter a minimum confidence value: "))
    print ("\n-------------------------------------------------\n")
    print ("\n-------------------Association Rules-------------------\n")
    items, transactions = read_data(location)
    out_file_name = location.replace(input_location, "")
    out_file_name = out_file_name.replace(".xlsx", "")
    run_Apriori(items, transactions, min_support, min_confidence, out_file_name)