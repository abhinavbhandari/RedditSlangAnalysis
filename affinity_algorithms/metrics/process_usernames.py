# This entire library can be implemented in C. 
import numpy as np
import multiprocessing as mp
import config
from affinity_aglorithms.utils.files import pickle_load
import os

def calculate_user_name_metrics(subname,
                                aff_word,
                                w2u_path,
                                u2w_path,
                                total_users,
                                intercepting_words=True):
    """Remove replacing w2u, and u2w at some point.
    
    Args:
        subname (str): Name of subreddit
        aff_word (list): List of affinity words
        w2u_path (str): Path to load w2u
        u2w_path (str): Path to load u2w
        total_users (int): Count of total users
        intercepting_words (bool): Whether to remove intercepting words. 
            Default is False
            
    Returns:
        A list of mean, std, slang_to_user_wc and percentage of users adopting slang.
    """
    num_of_users = []
    aff_value = []
    slang_to_user_wc = 0
    
    w2u = pickle_load(w2u_path)
    u2w = pickle_load(u2w_path)
    
    u2w, w2u = remove_intercepting_words(u2w, w2u)
    
    for w in aff_word: 
        if w in w2u:
            num_of_users.append(len(w2u[w]))
            slang_to_user_wc += 1
        else:
            num_of_users.append(0)
    
    mean = np.mean(num_of_users)
    std = np.std(num_of_users)
    user_percent = np.sum(num_of_users)/total_users
    
    return [mean, std, slang_to_user_wc, user_percent]


def calculate_user_name_metrics_mult(subnames, aff_word, subreddit_metrics):
    """Multiprocesses username metrics calculation.
    
    Calculates the number of affinty terms are adopted by users of a subreddit. Conducts this calculation
    for each subreddit that is passed, along with the list of affinity terms. The list of affinity terms
    is calcluated outside this function.
    The function also loads the word-2-user and user-2-word dictionaries internally.
    
    Args:
        subnames: list of subnames in str
        aff_word: list of affinity words (n most affinity words) for each subreddit
        subreddit_metrics: subreddit metrics obj, which contains loyalty, dedication, 
                no. of users, no. of comments,
    
    Returns:
        For each subreddit, it returns username to affinity term metrics such as
        mean, std, slang-to-user-wordcount, percentage of total users adopting slang. 
    """
    
    metrics_holder = []
    pool = mp.Pool(processes=7)
    for sub, aff_w in zip(subnames, aff_word):
        sub_path = os.path.join(config.SUBDIR_ANALYSIS_LOAD_PATH, sub)
        w2u_path = os.path.join(sub_path, sub + config.W2U_EXT)
        u2w_path = os.path.join(sub_path, sub + config.U2W_EXT)
        metrics_holder.append(pool.apply(calculate_user_name_metrics, 
                                         args=(sub, 
                                               aff_w,
                                               w2u_path,
                                               u2w_path,
                                               subreddit_metrics[sub])
                                        )
                             )
    return metrics_holder
    

def sorting_words_with_frequency(): 
    """Sort words of equal length by frequency.
    
    Todo:
        Implement this with sorted words, and frequency optimization. 
    """
    return None

 
def remove_intercepting_words(u2w, w2u):
    """Removes additional words that are not needed and act as fillers.
    
    Words such as "whenever" and "when" can be associated with the same user
    since "when" is found within "whenever". This should not be the case,
    and as a heuristic the longer word should be selected. This function mitgates
    that problem.
    
    Args:
        u2w (dic): Dictionary that maps usernames to words
        w2u (dic): Dictionary that maps words to usernames
        
    Returns:
        u2w, w2u
        
    Todo:
        Implement this with sorted words, and frequency optimization. 
    """
    w2u = w2u.copy()
    u2w = u2w.copy()
    
    for user, words in u2w.items():
        sorted_words = sorted(words, key=lambda x: len(x), reverse=True)
        remaining_text = user
        
        sorted_words_copy = sorted_words.copy()
        filtered_words = []
        for w in sorted_words:
            temp = remaining_text.replace(w, '')
            if temp is not remaining_text:
                remaining_text = temp
            else:
                sorted_words_copy.remove(w)
                w2u[w].remove(user)
        
        u2w[user] = sorted_words_copy
    return u2w, w2u


def tup_to_dic(tups,
               mult=False):
    """Converts a tuple to a dictionary"""
    if mult:
        dics = [{t[0]:t[1] for t in tup} for tup in tups]
        return dics
    else:
        return {t[0]:t[1] for t in tups}

    
def dic_to_tup(dics,
               mult=False):
    """Converts dictionary to a tuple"""
    tups = []
    if mult:
        for dic in dics:
            sub_tup = []
            for word in dic:
                sub_tup.append((word, dic[word]))
            tups.append(sub_tup)
    else:
        for word in dics:
            tups.append((word, dics[word]))
    return tups


def filter_words(tups,
                 word_len=[3, 4, 5],
                 word_freq=[[200], [15], [10]],
                 max_len=20, 
                 min_freq=5):
    """Filters words from tuples of (word, freq) of specified lengths. 
    
    Takes in various word lengths to which particular frequency thresholds
    need to be applied. There is little research conducted in what makes an
    accurate filter point for types of frequency. The word distribution of meaningless
    words needs to be investigated. Returns valid tuples, and rejected tuples.
    
    Args:
        tups (list): List of tuples
        word_len (list): List of length of words to which specified freq thresholds
            should be applied.
        max_len (int): Max length of word that should be accepted
        min_freq (int): Minimum frequency of words that should be accepted.
        
    Returns:
        list of tuples, and list of filtered tuples. 
    """
    remove_index = [ [] for i in range(len(tups))]
    
    for n, len_ in enumerate(word_len):
        # i represents the subreddit number
        for i, tup in enumerate(tups):
            # j represents the word number
            for j, t in enumerate(tup):
                if (len(t[0]) <= 2) or (len(t[0]) >= max_len):
                    remove_index[i].append(j)
                if len(t[0]) == len_:
                    if t[1] <= word_freq[n][i]:
                        remove_index[i].append(j)
                else:
                    if t[1] <= min_freq:
                        remove_index[i].append(j)
    
    remove_tups = [[] for i in range(len(remove_index))]
    for i, inds in enumerate(remove_index):
        accept_tups = []
        remove_set = set(inds)
        for j, tupd in enumerate(tups[i]):
            if j not in remove_set:
                accept_tups.append(tupd)
            else:
                remove_tups[i].append(tupd)
        tups[i] = accept_tups
    return tups, remove_tups


def conditional_insertion_in_dic(dic, term, insert_val):
    """If a term is in dictionary, append a value to it, or create a new entry."""
    if term in dic:
        dic[term].append(insert_val)
    else:
        dic[term] = [insert_val]


def create_user_to_word(usernames, word_dic):
    """Maps words in a subreddit to the users that use it in their usernames.
    
    Maps the words that are used in a dictionary by figuring out which 
    
    Args:
        usernames: a list of usernames
        word_dic: a dictionary of word to count. Key is word, val is count.
        
    Returns:
        Two dictionaries, that are username to words it contains, and words to usernames. 
    
    """
    word_to_user = {}
    user_to_word = {}
    for word in word_dic:
        for user in usernames:
            user = user.lower()
            if word in user:
#                 print(user, word)
                conditional_insertion_in_dic(word_to_user, word, user)
                conditional_insertion_in_dic(user_to_word, user, word)
    return word_to_user, user_to_word


def remove_words_not_in_dic(sub_dic, word_to_user, user_to_word):
    """Remove words in usernames that are not in dictionaries.
    
    Args:
        sub_dic (dic): Word -> count
        word_to_user (dic): Dictionary that maps word to user
        user_to_word (dic): Maps user to words
        
    State:
        Alters word_to_user and user_to_word. These are passed by reference.
    """
    word_set = set(word_to_user.keys())
    for word in word_set:
        if word not in sub_dic:
            for user in w2u[word]:
                if word in user_to_word[user]:
                    user_to_word[user].remove(word)
            del word_to_user[word]
                

def filter_correct_word_and_user(word_to_user, user_to_word, mult=True):
    """This algorithm takes in a wordToUser mapping annd filters correct usersToWord.
    
    The algorithm extracts each word and checks if there are words that it fits in.
    If there are terms that the selected word fits in, then it is removed.
    
    Args:
        word_to_user (dic): 
    """
    # key refers to one of the words a username is made up of.
    for key in word_to_user:
        users = word_to_user[key].copy()
        for user in users:
            words = user_to_word[user].copy()
            for word in words:
                if key in word and key != word:
                    if key in user_to_word[user]:
                        if key in user_to_word[user]:
                            user_to_word[user].remove(key)
                            word_to_user[key].remove(user)
    return word_to_user, user_to_word