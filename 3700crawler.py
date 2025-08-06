#!/usr/bin/env python3

#import The other Libraries I need
import argparse, socket, ssl, sys, threading
from html.parser import HTMLParser

#setting the recursion limit higher so that my program could run
sys.setrecursionlimit(10000)

DEFAULT_SERVER = "proj5.3700.network"
DEFAULT_PORT = 443

#declaring the html parser class
class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.flags = []
        self.collecting_flag = False
        
    # Looks for h3 and a tags to get links and flags
    def handle_starttag(self, tag, attrs):
        
        #if an h3 tag is found look for the secret flag and class attributes and set the collecting flag boolean to true
        if tag == 'h3':
            for attr, value in attrs:
                if attr == 'class' and value == 'secret_flag':
                    self.collecting_flag = True
        
        #if an a tag is found append the link to the links list
        elif tag == 'a':
            for attr in attrs:
                if attr[0] == 'href' and len(attr[1]) < 50:
                    self.links.append(attr[1])
    
    #checks if a flag is being collected currently and appends it to the flags list
    def handle_data(self, data):
        if self.collecting_flag:
            self.flags.append(data)
            self.collecting_flag = False

#declaring the Crawler class
class Crawler:
    #initalizing a crawler and it's fields to be utilized
    def __init__(self, args):
        self.server = args.server
        self.port = args.port
        self.username = args.username
        self.password = args.password
        self.flags = []
        self.visited = set()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_list = []
        self.max_threads = 5
        self.thread_pool = []
        self.lock = threading.Lock()

    #function that creates a wrapped tls socket for security
    #adds the new socket to the classes list of open sockets
    def create_wrapped_socket(self):
        #create the new socket
        mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        context = ssl.create_default_context()
        #wrap the socket
        wrapped = context.wrap_socket(mysocket, server_hostname= self.server)
        #connect the socket
        wrapped.connect((self.server, self.port))
        #append the socket to the list
        self.socket_list.append(wrapped)

    #extracts all of the cookies from a string of web content and returns them as a list
    def get_cookies(self, server_message):
        cookies = []
        words_list = server_message.split()
        #loop over all the strings from the server message
        for i in range(len(words_list)):
            #if a set-cookie is found add the next element of the words list to the cookie list
            if words_list[i] == "set-cookie:":
                cookies.append(words_list[i+1][10:-1])
            #if the middleman token is found add the next element of the words list to the cookie list
            elif words_list[i] == '''name="csrfmiddlewaretoken"''':
                cookies.append(words_list[i+1][7:-2])

        return cookies

    #gets the status of the message from the server and return it as an integer. If it's a 302 message return that as well as the new path to send
    def get_response_result(self, header):
        words = header.split()
        #try except block for if there is no result
        try:
            result = words[1]
            #check for 302 so that we can return the new path
            if result == "302":
                for i in range(len(words)):
                    if words[i] == "location:":
                        return [words[i + 1], 302]
            else:
                return int(result)
        #case of no result
        except:
            return 503
        
    #send a request to the server and recieve the data back returning the decoded data as a string
    def send_and_recieve_data_header(self, request, socket_index):
        #send the request to the socket determined by the parameter
        try:
            self.socket_list[socket_index].send(request.encode('ascii'))
        except:
            return
        #recive the data
        try:
            header_data, html_data = self.recieve_html_data(socket_index)
        except:
            return
        return header_data, html_data

    #recieve all the html data from the server. Seperates the header and the content and returns them as a touple
    def recieve_html_data(self, socket_index):
        header = b''
        content = b''
        content_length = -1
        #This while loop checks for whether the content length has been found yet
        while content_length == -1:
            #recive a chunk of data
            chunk = self.socket_list[socket_index].recv(1024)
            if not chunk:
                break
            header += chunk
            #find the end of the header
            header_end = header.find(b'\r\n\r\n')
            #if there is a header end then set the content length
            if header_end != -1:
                for header_line in header[:header_end].split(b'\r\n'):
                    if header_line.startswith(b'content-length:'):
                        content_length = int(header_line.split(b':', 1)[1].strip())
                        break
                #add to the content if any extra data was recieved besides the header
                content = header[header_end + 4:]
                #set the header
                header = header[:header_end]   
                
        #Once the content length has been found look for data until all the content has been recieved
        while len(content) < content_length:
            chunk = self.socket_list[socket_index].recv(min(1024, content_length - len(content)))
            
            if not chunk:
                break
            content += chunk
            
        #return the header and content decoded and as a touple
        return header.decode('utf-8'), content.decode('utf-8')



    #using a link and cookies create a get request for the server and return it
    def make_get_line(self, link, cookies):

        request = f"""GET {link} HTTP/1.1\r\nHost: www.3700.network\r\nConnection: keep-alive\r\nCookie: csrftoken={cookies[0]}; sessionid={cookies[1]}\r\n\r\n"""
        return request

    #check if a link is a valid fakebook link to be visited
    def is_fakebook_link(self, url):
        return url.startswith('/fakebook')

    #checks if a link has not been visited yet by checking the self.visited set
    def is_unvisited(self, url):
        return url not in self.visited
    
    #if the link is not a in the self.visited set then return true
    
    #Search some html and return a list of urls that have not been visited yet
    #While looking through the html look for secret flags. Dont for performance
    def get_page_links_and_find_flags(self, html_data):
        links = []
        #pass the html data to the html parser
        parser = MyHTMLParser()
        parser.feed(html_data)
        flags = parser.flags
        
        #if there are any flags look at them
        for flag in flags:
            with self.lock:
                cleaned_flag = flag[6:]
                #if there is a new flag print it and append it to the flags list
                if cleaned_flag not in self.flags:
                    print(cleaned_flag)
                    self.flags.append(cleaned_flag)
                    if len(self.flags) >= 5:
                        sys.exit(0)
        
        #if there are any links check that they're valid links to visited and add them to the links list
        for link in parser.links:
            if self.is_fakebook_link(link) and self.is_unvisited(link):
                links.append(link)
           
        #return the valid links
        return links


    #recursive function that searches through all the links for the secret flags.
    def visit_url(self, url_link, cookies):
        request = self.make_get_line(url_link, cookies)
            
        #gets the thread id to determine which socket to send to
        thread_id = int(threading.current_thread().name)
        
        #send the request for this url link. Recive the data from the server
        header_data, html_data = self.send_and_recieve_data_header(request, thread_id)
        message_result = self.get_response_result(header_data)

        #if the response if valid continue down the recursion
        if message_result == 200:
            links = self.get_page_links_and_find_flags(html_data)
            #immediately exit once all the flags are found
            if len(self.flags) == 5:
                sys.exit(0)
                
            #lock the visted set so only one thread can access it and duplicate links aren't added
            with self.lock:
                self.visited.update(links)
            
            #implemented recursion. Visit all the valid links that were found on the page
            for link in links:
                self.visit_url(link, cookies)
        
        #exit the funciton on error
        elif message_result == 403 or 404:
            return

        #retry this link on 503
        elif message_result == 503:
            self.visit_url(url_link, cookies)
        
        #create a new socket if a socket timeout is reached
        elif message_result == 408:
            #create new socket resend the request
            self.socket = self.create_wrapped_socket()
            self.visit_url(url_link, cookies)

        #if the response is 302 then follow the redirect
        elif isinstance(message_result, list):
            self.visit_url(message_result[0], cookies)
        #check for edge case and return
        else:
            return
            
    #Starts the web crawl after the login has been done and visits all the urls on the inital page
    def crawl(self, html_data, cookies):
        #hard code the initial url after login
        request = self.make_get_line("/fakebook/", cookies)
        header_data, html_data = self.send_and_recieve_data_header(request, 0)
        links = self.get_page_links_and_find_flags(html_data)
        #loop over all the intial links found
        for link in links:
            #only one thread can create more threads at a time
            with self.lock:
                if len(self.thread_pool) < self.max_threads:
                    #create a thread for the visit url method. Name it with the number of threads
                    thread = threading.Thread(target=self.visit_url, args=(link, cookies), name = str(len(self.thread_pool)))
                    self.create_wrapped_socket()
                    thread.start()
                    self.thread_pool.append(thread)
                #just in case the sys.exit(0) doensn't trigger in a thread clean up all the threads.
                if len(self.flags) == 5:
                    for thread in self.thread_pool:
                        thread.join()
                    return
        
    #The function used to get the homepage and log into the server
    def run(self):
        request = "GET /accounts/login/?next=/fakebook/ HTTP/1.1\r\nHost: www.3700.network\r\nConnection: keep-alive\r\n\r\n"

        #create the first socket and send the request
        self.create_wrapped_socket()
        header_data, html_data = self.send_and_recieve_data_header(request, 0)
        #get the cookies and middle ware token
        cookies = self.get_cookies(header_data)
        token = self.get_cookies(html_data)
        cookies.append(token[0]) 

        #make the login message
        content = f"""username={self.username}&password={self.password}&csrfmiddlewaretoken={cookies[2]}&next=/fakebook/"""
        request = f"""POST /accounts/login/?next=/fakebook/ HTTP/1.1\r\nHost: www.3700.network\r\nConnection: keep-alive\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: {len(content)}\r\nCookie: sessionid={cookies[1]}; csrftoken={cookies[0]}\r\n\r\nusername={self.username}&password={self.password}&csrfmiddlewaretoken={cookies[2]}&next=/fakebook/\r\n\r\n"""

        #get the response from the login.
        header_data, html_data = self.send_and_recieve_data_header(request, 0)
        #get the second set of cookies to be used for the rest of the program
        cookies = self.get_cookies(header_data)
        #start the crawl
        self.crawl(html_data, cookies)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='crawl Fakebook')
    parser.add_argument('-s', dest="server", type=str, default=DEFAULT_SERVER, help="The server to crawl")
    parser.add_argument('-p', dest="port", type=int, default=DEFAULT_PORT, help="The port to use")
    parser.add_argument('username', type=str, help="The username to use")
    parser.add_argument('password', type=str, help="The password to use")
    args = parser.parse_args()
    sender = Crawler(args)
    sender.run()
