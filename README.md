# Fakebok Crawler - Web crawler to find hidden data 

## Introduction

This is a project I completed as part of my Computer Networks class. It crawls a knockoff faceboook called fakebook looking through html
for secret flags unique to my student login.

## Implmentation details:

I implemented a depth first search algorithm with multi threading to solve this problem.
The main challenge of the web crawler was making sure every web page was visited so that they could be parsed for the hidden flags.
Recursion was a good solution because it automatically kept track of all of the links that could be visited from the current page.
The trouble with visiting all the links was thier web like nature. I couldn't just save all the links on a page visit them and then
be done. I had to get the links from a page visit and then visit them and that next visit could also have unvisited links so I had to
get those as well and so on. 
The rest of my design decisions were made around the recursion implementation. 
So I used a set to make sure links weren't being revisited if they had already been visited, stopping circular visiting of
pages.
Helper functions were created for repeated actions like creating and wrapping sockets, sending or receiving data or getting 
unvisited links on a page.
I used the HTMLParser library to parse the HTML since building a custom parser was outside of the scope of this project.

### Threading

I had to implement threading because my programming was timing out on the submission website even though all of the logic was correct.
A new socket is created for each thread so they could send messages to the server independently.
The set of visited links was locked when accessed to prevent a data race on the set which would be duplicate links being added.
I was limited to 5 threads per the project specs.

## Approach explained:

I went about implementing my program in the same order that it would run.
This made my program easy to test because the most recent data was always the most helpful. 
If an error caused an exit I knew the most recent data was were the error had occured.
Or if there was unexpected behavior I could just look at the most recent data to see where my program had gone wrong.
This was very helpful in a long running program sending and recieveing a lot of data. I didn't have to search around a lot
of text to find unexpected behavior or errors.
It was also helpful to not design the system before actually testing how it behaved and what the problems were going to be.
My programs is designed to solve the problem of finding the secret flags not to adhere to some strucutre I made prematurely.

### Language

I used python at the recomendation of my professor. He suggested this because of its ease of use and to make sure we were 
implementing networking algorithms and concepts not parsing data specific to any one language. 

## Testing

I did my testing through print statements. For some reason the VSCode debugger was very buggy when trying to step through my code 
at run time. 
I had the sent and received messages print out when I was working out that logic.
Then if my functions were buggy I would print them out step by step so I could see exactly what the implemention was doing.
However the good thing about html is that it's really just formatted text so it lends itself to print debugging.
Then I could fix it and test it again by looking at a the logic or messages again.
