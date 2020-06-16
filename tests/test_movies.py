from src.helpers import merge
from assertpy import assert_that

def test_merge_two_movie_lists():
    #given two movie list
    list1 = ['A','B','C','1unique_to_list1','2unique_to_list1']
    list2 = ['A','B','C','1unique_to_list2','2unique_to_list2']
    # when I merger the two lists
    result = merge(list1,list2)
    # then
    assert_that(result).is_equal_to(['A','B','C'])

