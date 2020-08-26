import restricted_words as restricted_words_list
import pandas as pd
from nltk.stem.porter import PorterStemmer
import time 

LOG_FILE = None

STRICT = 'strict'
FUZZY = 'fuzzy'

def import_dataset(dataset_path):
    
    dataset, label_dict, value_label_dict = False, False, False
    raise_error = False
    status_message = False

    if dataset_path.endswith(('"', "'")):
        dataset_path = dataset_path[1:-1] 

    dataset_path_l = dataset_path.lower()

    try:
        if dataset_path_l.endswith(('xlsx', 'xls')):
            dataset = pd.read_excel(dataset_path)
        elif dataset_path_l.endswith('csv'):
            dataset = pd.read_csv(dataset_path)
        elif dataset_path_l.endswith('dta'):
            try:
                dataset = pd.read_stata(dataset_path)
            except ValueError:
                dataset = pd.read_stata(dataset_path, convert_categoricals=False)
            label_dict = pd.io.stata.StataReader(dataset_path).variable_labels()
            try:
                value_label_dict = pd.io.stata.StataReader(dataset_path).value_labels()
            except AttributeError:
                status_message = "No value labels detected. " # Not printed in the app, overwritten later.
        elif dataset_path_l.endswith(('xpt', '.sas7bdat')):
            dataset = pd.read_sas(dataset_path)
        elif dataset_path_l.endswith('vc'):
            status_message = "**ERROR**: This folder appears to be encrypted using VeraCrypt."
            raise Exception
        elif dataset_path_l.endswith('bc'):
            status_message = "**ERROR**: This file appears to be encrypted using Boxcryptor. Sign in to Boxcryptor and then select the file in your X: drive."
            raise Exception
        else:
            raise Exception

    except (FileNotFoundError, Exception):
        if status_message is False:
            status_message = '**ERROR**: This path appears to be invalid. If your folders or filename contain colons or commas, try renaming them or moving the file to a different location.'
        raise

    if (status_message):
        log_and_print("There was an error")
        log_and_print(status_message)
        return (False, status_message)

    print('The dataset has been read successfully.\n')
    dataset_read_return = [dataset, dataset_path, label_dict, value_label_dict]
    return (True, dataset_read_return)


# def initialize_lists(function_pipe = None):

#     possible_pii = []
#     global yes_strings
#     yes_strings = ['y', 'yes', 'Y', 'Yes']

#     list_restricted_words = restricted_words.get_restricted_words()
    
#     smart_return([possible_pii, list_restricted_words], function_pipe)


def add_stem_of_words(restricted):
# Identifies stems of restricted words and adds the stems to restricted list

    initialized_stemmer = PorterStemmer()
    restricted_stems = []
    for r in restricted:
        restricted_stems.append(initialized_stemmer.stem(r).lower())

    restricted = restricted + restricted_stems
    restricted = list(set(restricted))
    
    return restricted


def word_match(column_name, restricted_word, type_of_matching):
    if(type_of_matching == STRICT):
        return column_name.lower() == restricted_word.lower()
    else: # type_of_matching == FUZZY
        #Check if restricted word is inside column_name
        return restricted_word.lower() in column_name.lower()

def find_piis_word_match(dataset, label_dict, sensitivity = 3, stemmer = None):
    #Piis will be identifiy both by strict or fuzzy matching with predefined list of words

    pii_strict_restricted_words = restricted_words_list.get_strict_restricted_words()
    pii_fuzzy_restricted_words = restricted_words_list.get_fuzzy_restricted_words()

    #We will save all restricted words in a dictionary, where the keys are the words and their values is if we are looking for a strict or fuzzy matching with that word
    restricted_words = {}
    for word in pii_strict_restricted_words:
        restricted_words[word] = STRICT
    for word in pii_fuzzy_restricted_words:
        restricted_words[word] = FUZZY


    #Currently not doing any stem matching
    #Get stem of the restricted words
    #pii_restricted_words = add_stem_of_words(pii_restricted_words)

    # Looks for matches between column names (and labels) to restricted words
 
    possible_pii = {}
    log_and_print("List of identified PIIs: ")

    #For every column name in our dataset
    for column_name in dataset.columns:
        #For every restricted word
        for restricted_word, type_of_matching in restricted_words.items():
            #Check if restricted word is in the column name
            if word_match(column_name, restricted_word, type_of_matching):

                log_and_print("Column '"+column_name+ "' considered possible pii given column name had a "+type_of_matching+" match with restricted word '"+ restricted_word+"'")
                
                possible_pii[column_name] = "Name had "+ type_of_matching + " match with restricted word '"+restricted_word+"'"

                #If found, I dont need to keep checking this column with other restricted words
                break

            #If dictionary of labels is not of booleans, check labels
            if type(label_dict) is not bool:
                
                #Check words of label of given column
                column_label = label_dict[column_name]
               
                if word_match(column_label, restricted_word, type_of_matching):
                    log_and_print("Column '"+column_name+ "' considered possible pii given column label '"+column_label+"' had a "+type_of_matching+" match with restricted word '"+ restricted_word+"'")
                    
                    possible_pii[column_name] = "Label had "+ type_of_matching + " match with restricted word '"+restricted_word+"'"
                    break
    return possible_pii


def log_and_print(message)    :
    file = open(LOG_FILE, "a") 
    file.write(message+'\n') 
    file.close() 
    print(message)

def split_by_word(search_term):
    return search_term.replace('-', ' ').replace('_', ' ').replace('  ', ' ').replace('  ', ' ').split(' ')

# def is_acronym(acronym, text):
#     text = text.lower()
#     acronym = acronym.lower()
#     text = split_by_word(text)
#     count = 0
    
#     for c in range(len(acronym)):
#         try:
#             if acronym[c] == text[c][0]:
#                 count += 1
#         except IndexError:
#             return False
#     if count == len(acronym):
#         return True
#     else:
#         return False
    
def levenshtein_distance(first, second):
    # Find the Levenshtein distance between two strings.
    insertion_cost = .5
#     if not is_acronym(first, second):
#         insertion_cost = .2
#         first = first.lower()
#         if first[-1] == 's':
#             if is_acronym(first.rstrip('s'), second):
#                 insertion_cost = 0
    
    first = first.lower()
    second = second.lower()
    if len(first) > len(second):
        first, second = second, first
    if len(second) == 0:
        return len(first)
    first_length = len(first) + 1
    second_length = len(second) + 1
    distance_matrix = [[0] * second_length for x in range(first_length)]
    for i in range(first_length):
        distance_matrix[i][0] = i
        for j in range(second_length):
            distance_matrix[0][j]=j
    for i in range(1, first_length):
        for j in range(1, second_length):
            deletion = distance_matrix[i-1][j] + 1
            insertion = distance_matrix[i][j-1] + insertion_cost
            substitution = distance_matrix[i-1][j-1]
            if first[i-1] != second[j-1]:
                substitution += 1
            distance_matrix[i][j] = min(insertion, deletion, substitution)
    return distance_matrix[first_length-1][second_length-1]

def compute_fuzzy_scores(search_term, restricted):
    match_list = []
    match_score_list = []
    for r in restricted:
        match_list.append(r)
        match_score_list.append(levenshtein_distance(search_term,r))   
    #print(match_list, match_score_list)
    return [match_list, match_score_list]

def best_fuzzy_match(word_list, score_list): #would eliminate this by implementing a priority queue
    lowest_score_index = score_list.index(min(score_list)) #index of lowest (best) score
    best_word_match = word_list[lowest_score_index] #use index to locate the best word
    del score_list[lowest_score_index] #remove the score from the list
    word_list.remove(best_word_match) #remove the word from the list
    return [best_word_match, word_list, score_list] #return the best word

def ordered_fuzzy_results(word_list, score_list):
    ordered_fuzzy_list = []
    ordered_score_list = []
    best_fuzzy_results = ['', word_list, score_list] #initial set_up for while loop call        
    while len(word_list) > 0:
        best_fuzzy_results = best_fuzzy_match(best_fuzzy_results[1], best_fuzzy_results[2])
        ordered_fuzzy_list.append(best_fuzzy_results[0])
        #ordered_score_list.append(best_fuzzy_results[2][word_list.index(best_fuzzy_results[0])])
    return ordered_fuzzy_list[:5]

def run_fuzzy_query(term, fuzzy_threshold, restricted):
    fuzzy_result = []
    words = split_by_word(term)
    for w in words:
        if len(w) <= 2:
            continue
        scored_list = compute_fuzzy_scores(w, restricted)
        if min(scored_list[1]) < fuzzy_threshold:
            final_result = ordered_fuzzy_results(scored_list[0], scored_list[1])
            fuzzy_result.append(final_result[0])
            
#     scored_list = compute_fuzzy_scores(term)
#     if min(scored_list[1]) < fuzzy_threshold:
#         final_result = ordered_fuzzy_results(scored_list[0], scored_list[1])
#         fuzzy_result.append(final_result[0])
        
    if len(fuzzy_result) == 0:
        return False
    else:
        return fuzzy_result
    #return final_result


# In[7]:

def fuzzy_partial_stem_match(possible_pii, restricted, dataset, stemmer, threshold = 0.75, function_pipe = None, messages_pipe = None):
# Looks for fuzzy and intelligent partial matches
# Recommended value is 0.75. Higher numbers (i.e. 4) will identify more possible PII, while lower numbers (i.e. 0.5) will identify less potential PII.

    smart_print('The fuzzy and intelligent partial matches with stemming algorithm is now running.', messages_pipe)

    for v in tqdm(dataset.columns):
        if run_fuzzy_query(v.lower(), threshold, restricted) != False:
            possible_pii.append(v)
        if run_fuzzy_query(stemmer.stem(v).lower(), threshold, restricted) != False:
            possible_pii.append(v)
            
    smart_print('**' + str(len(set(possible_pii))) + '**' + " total fields that may contain PII have now been identified.", messages_pipe)

    smart_return(possible_pii, function_pipe)


# # All Uniques

# In[8]:

def unique_entries(dataset, min_entries_threshold = 0.5):
    #Identifies pii based on columns having only unique values
    #Requires that at least 50% of entries in given column are not NA   

    possible_pii={}
    for v in dataset.columns:

        n_not_na_rows = len(dataset[v].dropna())
        n_unique_entries = dataset[v].nunique()

        #If all rows are empty, dont check column
        if(n_not_na_rows==0):
            continue

        at_least_50_p_not_NA = n_not_na_rows/len(dataset) > min_entries_threshold

        if n_not_na_rows == n_unique_entries and at_least_50_p_not_NA:
            
            log_and_print("Column '"+v+"' considered possible pii given all entries are unique")
            possible_pii[v] = "Column entries are unique"

        #We will not ask absolute unique values, but rather than the amount of unique values is very high
        elif n_unique_entries/n_not_na_rows>0.7:
            possible_pii[v] = "Column entries are sparse strings (>70%)"
            log_and_print("Column '"+v+"' considered possible pii given 70% of entries are unique")

    return possible_pii


def find_columns_with_phone_numbers(dataset):

    columns_with_phone_numbers = {}

    phone_n_regex_expression = "(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})"

    for column in dataset.columns:

        #Check that all values in column are not NaN
        if(pd.isnull(dataset[column]).all() == False):

            #Find first 10 values that are not NaN nor empty space ''
            column_with_no_nan = dataset[column].dropna()
            column_with_no_empty_valyes = column_with_no_nan[column_with_no_nan != '']
            first_10_values = column_with_no_empty_valyes.iloc[0:10]

            match_result = first_10_values.astype(str).str.match(pat = phone_n_regex_expression)
            #If all not NaN values matched with regex, save column as PII candidate
            if(any(match_result)):
                log_and_print("Column '"+column+"' considered possible pii given column entries have phone number format")
                columns_with_phone_numbers[column]= "Column entries have phone number format"

    return columns_with_phone_numbers


def format_detection(dataset):
    
    #Find columns with phone numbers formats
    possible_pii = find_columns_with_phone_numbers(dataset)

    #Check other formats

    return possible_pii


def export_encoding(dataset_path, encoding_dict):
    encoding_file_path = dataset_path.split('.')[0] + '_encodingmap.csv'

    encoding_df = pd.DataFrame(columns=['variable','orginial value', 'encoded value'])

    for variable, values_dict in encoding_dict.items():
        for original_value, encoded_value in values_dict.items():
            encoding_df.loc[-1] = [variable, original_value, encoded_value]
            encoding_df.index = encoding_df.index + 1
    encoding_df.to_csv(encoding_file_path, index=False)

def create_anonymized_dataset(dataset, label_dict, dataset_path, pii_candidate_to_action):

    #Drop columns
    columns_to_drop = [column for column in pii_candidate_to_action if pii_candidate_to_action[column]=='Drop']

    dataset.drop(columns=columns_to_drop, inplace=True)
    log_and_print("Dropped columns: "+ " ".join(columns_to_drop))

    #Encode columns
    columns_to_encode = [column for column in pii_candidate_to_action if pii_candidate_to_action[column]=='Encode']

    if(len(columns_to_encode)>0):
        log_and_print("Will encode following columns: "+ " ".join(columns_to_encode))
        dataset, encoding_used = recode(dataset, columns_to_encode)
        log_and_print("Map file for encoded values created.")
        export_encoding(dataset_path, encoding_used)

    exported_file_path = export(dataset, dataset_path, label_dict)

    return exported_file_path

def find_piis(dataset, label_dict):
    
    all_piis_detected = {}

    #Another thing that might be tried
    #fuzzy_partial_stem_match()    

    #Find piis based on unique_entries detections
    piis_unique_entries = unique_entries(dataset)

    #Find piis based on entries format
    piis_suspicious_format = format_detection(dataset)

    #Find piis based on word matching
    piis_word_match = find_piis_word_match(dataset, label_dict)

    all_piis_detected.update(piis_suspicious_format)
    all_piis_detected.update(piis_unique_entries)
    all_piis_detected.update(piis_word_match)

    return all_piis_detected

def create_log_file_path(dataset_path):

    dataset_directory_path = "/".join(dataset_path.split('/')[:-1])
    
    file_name = dataset_path.split('/')[-1].split('.')[0]

    global LOG_FILE
    LOG_FILE = dataset_directory_path+"/log_"+file_name+str(time.time()).replace('.','')+'.txt'

    print(LOG_FILE)


def read_file_and_find_piis(dataset_path):
    
    create_log_file_path(dataset_path)

    #Read file
    import_status, import_result = import_dataset(dataset_path)    
    if import_status is False:
        return import_status, import_result, _, _
    
    dataset, dataset_path, label_dict, value_label_dict = import_result

    #Find piis
    piis = find_piis(dataset, label_dict)

    log_and_print("Identified PIIs: "+" ".join(list(piis.keys())))

    return True, piis, dataset, label_dict



def recode(dataset, columns_to_encode):

    #Keep record of encoding
    econding_used = {}

    for var in columns_to_encode:

        # dataset = dataset.sample(frac=1).reset_index(drop=False) # reorders dataframe randomly, while storing old index
        # dataset.rename(columns={'index':var + '_index'}, inplace=True)

        # Make dictionary of old and new values
        new_value = 1
        old_to_new_dict = {}   
        for unique_val in dataset[var].unique():
            old_to_new_dict[unique_val] = new_value
            new_value += 1

        # Replace old values with new in dataframe
        for k, v in old_to_new_dict.items():
            dataset[var].replace(to_replace=k, value=v, inplace=True)

        # Alternative approach, likely to be significantly quicker. Replaces the lines that employ values_dict.
        #dataset[var] = pd.factorize(dataset[var])[0] + 1

        log_and_print(var + ' has been successfully encoded.')
        econding_used[var] = old_to_new_dict

    return dataset, econding_used


# In[13]:

def export(dataset, dataset_path, variable_labels = None):

    dataset_type = dataset_path.split('.')[1]

    if(dataset_type == 'csv'):
        new_file_path = dataset_path.split('.')[0] + '_deidentified.csv'
        dataset.to_csv(new_file_path, index=False)

    elif(dataset_type == 'dta'):
        new_file_path = dataset_path.split('.')[0] + '_deidentified.dta'

        try:
            dataset.to_stata(new_file_path, variable_labels = variable_labels, write_index=False)
        except:
            dataset.to_stata(new_file_path, version = 117, variable_labels = variable_labels, write_index=False)
            

    elif(dataset_type == 'xlsx'):
        new_file_path = dataset_path.split('.')[0] + '_deidentified.xlsx'
        dataset.to_excel(new_file_path, index=False)

    elif(dataset_type == 'xls'):
        new_file_path = dataset_path.split('.')[0] + '_deidentified.xls'
        dataset.to_excel(new_file_path, index=False)

    else:
        log_and_print("Data type not supported")
        new_file_path = None
            
    return new_file_path


def main_when_script_run_from_console():
    dataset_path = 'test_files/cases_1.csv'

    reading_status, pii_candidates_or_message, dataset, label_dict = read_file_and_find_piis(dataset_path)

    #Check if reading was succesful
    if(reading_status is False):    
        error_message = pii_candidates_or_message
        log_and_print(error_message)
        return
    else:
        pii_candidates = pii_candidates_or_message

    #Manually set action for piis
    pii_candidates_to_action ={}
    for pii in pii_candidates:
        pii_candidates_to_action[pii] = 'Drop'

    create_anonymized_dataset(dataset, label_dict, dataset_path, pii_candidates_to_action)


if __name__ == "__main__":
    main_when_script_run_from_console()


