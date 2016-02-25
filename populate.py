from bs4 import BeautifulSoup
import sqlite3
import requests
import re
import os
import random
import time
import sys


ext = [
    'A',
    'B',
    'C',
    'D',
    'E-F',
    'G',
    'H',
    'I-J',
    'K',
    'L',
    'M',
    'N-O',
    'P',
    'Q-R',
    'S',
    'T-V',
    'W-Z',
    'Collaborations']


# create a file txt to store wiki link of people initial names
def list_people_by_name():
    s = requests.session()
    html = s.get('https://en.wikiquote.org/wiki/List_of_people_by_name')
    if html is not None:
        soup = BeautifulSoup(html.text, 'lxml')
        cat = soup.findAll('center')
        a = re.findall(r'href="(\S+)"', str(cat))
        i = 0

        f = open('List_people_by_name.txt', 'w')
        while True:
            try:
                print(a[i])
                f.write('https://en.wikiquote.org' + a[i] + '\r\n')
                print('---------------')
                i += 1
            except Exception:
                break
        f.close()
        s.close()
    return


# create n files with all names belonging at a certain name initial family
def people():
    s = requests.session()
    with open('List_people_by_name.txt', 'r') as f:
        for lines in f:

            pos = lines.find('wiki/')
            if pos != -1:
                if os.path.isfile(lines[pos + 5:].replace(',', '').strip()):
                    print(
                        lines[
                            pos +
                            5:].replace(
                            ',',
                            '').strip() +
                        ' already created!')
                    continue

                f1 = open(lines[pos + 5:].replace(',', '').strip(), 'w')
                page = s.get(lines.strip())
                soup = BeautifulSoup(page.text, 'lxml')
                if soup:
                    name = soup.findAll('a', href=True)
                    for n in name:
                        nhref = n.get('href')
                        if re.match(r'.wiki/\w+_[a-z]+', str(nhref.lower())):
                            if nhref.lower().find('list') == -1:
                                if nhref.lower().find('main') == -1:
                                    print(nhref)
                                    f1.write(n.get('href') + '\r\n')

            f1.close()

    s.close()


# Create a file with 10 random name that begin with 10 random initials
def random_quotes():
    if os.path.isdir('Random_files') is False:
        os.mkdir(os.getcwd() + '/Random_files')

    frn = 'Random_people_' + str(time.time())  # filename of random people
    f_rand_quote = open(os.getcwd() + '/Random_files/' + frn, 'w')

    for i in range(10):  # if you want more or less people
        num = random.randrange(0, len(ext))  # random name initial
        fn = 'List_of_people_by_name_' + ext[num]
        print("Drawed: " + fn)
        f_rand_quote.write(fn + '\r\n')
        if os.path.isfile(fn) is False:
            print('Missing file:' + fn)
            break
        names_list = []
        with open(fn, 'r') as f:
            for lines in f:
                names_list.append(lines.strip())
        for j in range(10):  # if you want more or less people
            num = random.randrange(0, len(names_list))
            print(names_list[num])
            f_rand_quote.write(names_list[num] + '\r\n')
    print('')
    f_rand_quote.close()
    return frn


def quotes(fname):  # get all quotes for each name

    conn = sqlite3.connect('WIKI_QUOTES.db')
    c = conn.cursor()
    s = requests.session()

    for fn in fname:
        quotes_list = []
        print("""From the file below, every quote will be
               scraped for each name present!""")
        print(fn)
        time.sleep(2)

        if len(fname) < 2:
            fn = os.getcwd() + '/Random_files/' + fn
       
        with open(fn, 'r') as f:
            for lines in f:
                quotes_list = []
                print(lines.strip())
                if lines.find('wiki') != -1:
                    name = str(lines.strip()[6:])
                    query = """SELECT who FROM quotes WHERE who = '%s';""" % name
                    result = c.execute(query)
                    print('Checking for quotes of: ' + name)
                    if result.fetchone() is not None:
                         print(name + ': already scraped!')
                         print('~' * 40)
                         continue
         
                    page = s.get('https://en.wikiquote.org/wiki/' + name)
                    print(page)
                    soup = BeautifulSoup(page.text, 'lxml')
                    nodo = soup.find('span', {'id': 'Quotes'})
                    if nodo is None:
                        print('No quotes for ' + name)
                        print('')
                        continue  # pass to next name

                    print('Scraping is running for ' + name)
                    nextn = nodo.findNext('ul')  # next quote
                    while True:
                        sys.stdout.write('.')  # print a dot for each quote
                        # nextn example content
                        # <ul>
                        # <li><i>Autoritätsdusel i.... <-- help[1] 
                        # <ul>
                        # <li>Unthinking respect for authority...
                        # <li>Letter to Jost Winteler (1901),...</li>
                        # </ul>
                        # </li>
                        # </ul>
                        help = str(nextn).strip().split('\n')
                        try:
                            # check for the quote <li> tag in list pos 1
                            # if yes extract the quote and remove tags
                            if help[1].find('<li>') != -1:
                                q = help[1][help[1].find('<li>') + 4:]
                                quotes_list.append(re.sub('<[^>]*>', '', q))
                        except:
                            pass
 
                        # end of "Quotes" section                      
                        if str(nextn).find('id="About"') != - \
                                1 or str(nextn).find('id="External_links"') != -1:
                            print('\nNo more Quotes!')
                            break
                        try:
                            nextn = nextn.next_sibling
                        except Exception:
                            print("""Exception occured, maybe end of the DOM
                                  wo About or External_links""")
                            break

                    
                    # the quotes will be stored in a blob field, "|" used to
                    # keep separate each quote
                    
                    try:
                        c.execute(
                            """INSERT INTO quotes (who, qlist) VALUES(?, ?);""",
                            (name,
                            "|".join(quotes_list)))
                        conn.commit()
                    except Exception:
                        print('Error INSERT query!')
                    finally:
                        print('Added quotes to WIKI_QUOTES.db for: ' + name) 
                        print('')
                        print('~' * 40)
    s.close()
    conn.close()
    return


def main():
    args = sys.argv[1:]

    if not args:
        print('usage: [--random] [--all]')
        print('')
        print("""[--random] if you want to extract 10 name from 10 name
              initial raffle --> 100 names in total""")
        print('[--all] all names --> a lot, never tried')
        sys.exit(1)

    # Notice the summary flag and remove it from args if it is present.
    random1 = False
    all1 = False
    if args[0] == '--random':
        random1 = True
        del args[0]
    elif args[0] == '--all':
        all1 = True
        del args[0]
    else:
        print('Select the option!')
        quit()
    # txt file that contains link name initial
    if os.path.isfile(
            'List_people_by_name.txt') is False:
        print('Crea il file uno')
        list_people_by_name()

    people()  # create n files for each name in initial family link
    print('')

    if random1:
        print('Random mode! - Enter to continue...')
        input()
        f_name = []
        f_name.append(random_quotes())
        quotes(f_name)

    if all1:
        f_name = []
        for f in os.listdir():
            if re.match(r'List_of\w+', f):
                f_name.append(f)
        f_name.sort()
        quotes(f_name)  # scrape quotes for everyone

    return

if __name__ == '__main__':
    main()

