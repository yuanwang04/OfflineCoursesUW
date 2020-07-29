'''
    This project will gets all in person courses in UW, 2020 Fall.
    Output to data.json / data.csv with each course's name, SLN, credit, and type.

    Malicious and/or commercial uses are forbidden.

    Yuan 2020/07
'''

import requests
from bs4 import BeautifulSoup
import re
import json
import csv

URL_ROOT = "https://www.washington.edu/students/timeschd/AUT2020/"
COURSE_NUM_LIMIT = 499
JSON_PATH = 'data.json'
CSV_PATH = 'data.csv'

'''
    Returns a list of links' suffix to each departments' available courses
    e.g. math.html
'''
def get_links():
    html = requests.get(url=URL_ROOT).text
    soup = BeautifulSoup(html, features='lxml')

    hrefs = soup.find_all('a', attrs={'href': re.compile('^[a-z]*\.html')})
    links = []
    for l in hrefs:
        links.append(l['href'])

    return links


'''
    Gets all in person courses's name with corresponding section numbers
    whose levels are below @COURSE_NUM_LIMIT. Also get the courses' corresponding 
    credit and category.
    
    @end: String, the department from which courses are fetched, e.g. 'math.html'
    @return: a dictionary with keys='{course_name} {credit} {type}', values
        as a list of section numbers. 
'''
def get_course(end):
    #Get soups
    url = URL_ROOT + end
    html = requests.get(url=url).text
    soup = BeautifulSoup(html, features='lxml')
    html2 = requests.get('http://www.washington.edu/students/crscat/' + end).text
    credit_soup = BeautifulSoup(html2, features='lxml')

    courses = soup.find_all('table', attrs={'width': '100%'})
    in_person = {}
    i = 2 #ignore previous blocks
    course_name = ""
    while (i < len(courses)):
        course = courses[i]
        if ('bgcolor' in course.attrs and course['bgcolor']=='#ffcccc'): # if it is course_name block
            course_name = course.find('a', attrs={'name': re.compile('.*')})['name']
            num = int(course_name[len(course_name)-3:len(course_name)])
            print('current course: ' + course_name)
            if (num > COURSE_NUM_LIMIT): # ignore remaining courses which are above COURSE_NUM_LIMIT
                break
            else: # get credit and type, integrate into course name
                address = course.find('a', attrs={'href': re.compile('/students/crscat/.*')})['href']
                crdt = get_credit(credit_soup, course_name)
                type = get_type(course)
                course_name += ' ' + crdt + ' ' + type
                i += 1
        else: # section block
            if (check_in_person(course)):
                course_num = course.find('a').string
                if (course_name not in in_person): # add to result
                    in_person[course_name] = []
                in_person[course_name].append(course_num)
            i += 1
    return in_person


'''
    Checks if the given @course (as a soup element) is in person.
    Return true if in person. 
'''
def check_in_person(course):
    if (course.find('a', attrs={'href': re.compile('.*maps.*')}) is None):
        return False
    contents = course.find('pre').contents
    if ('VIA REMOTE' in contents[2]):
        return False
    if (len(contents) > 4 and 'VIA REMOTE' in contents[4]):
        return False
    return True

'''
    Get the credit of the given course @name from the given @soup
    @return 0 if no course was found.
    
    @soup: the department's credit page's soup
    @name: String, course name
'''
def get_credit(soup, name):
    tag = soup.find('a', attrs={'name': name})
    if (tag is None):
        return '0'
    full_title = tag.find('b').string
    tpl = re.findall('\(\d.*\)', full_title)
    if (tpl is not None and len(tpl) > 0):
        return tpl[0][1]
    else:
        return '0'

'''
    Get the course's category from the given @course
    
    @course: soup's course title element
'''
def get_type(course):
    b = course.find_all('b')
    if (b is None or len(b) < 2):
        return 'N/A'
    else:
        type = b[1].string
        if (type is None):
            return 'N/A'
        return type[1:len(type)-1]

'''
    Writes the given dictionary to JSON_PATH
'''
def write_to_json(in_person):
    with open(JSON_PATH, 'w') as fp:
        json.dump(in_person, fp, sort_keys=True, indent=4)

'''
    Writes the given dictionary to CSV_PATH
'''
def write_to_csv(in_person):
    with open(CSV_PATH, 'w', newline='') as csvfile:
        fieldnames = ['course_num', 'credits', 'type', 'SLN']
        writer = csv.writer(csvfile)
        writer.writerow(fieldnames)
        for key in in_person.keys():
            values = in_person[key]
            arr = key.split()
            arr.append('0')
            for value in values:
                arr[3] = value
                writer.writerow(arr)

'''
    Runs the program, get all links and fetch all in person courses, 
    output to json and csv
'''

def main():
    links = get_links()
    in_person = {}
    for link in links:
        new_in_person = get_course(link)
        in_person.update(new_in_person)

    write_to_json(in_person)
    write_to_csv(in_person)

main()




