Note:
>> I have successfully completed BONUS questions, so it includes deleting tweets and logout
>> If one of the worker dies, and can reconnect
>> It's able to handle 1 to n worker
>> It is also load balancing across workers using random method
>> Front end and back end works very well alltogether
>> When we log out, it goes directly to main page as included in BONUS questions
>> According to rubric's point :GET/POST /api/tweet return appropriate error message when not logged 
   to test this point, don not log out from screen, but right click->inspect->application->cookies->delete username manually from there
   and try to post tweet on screen, it will give error message



##########################################################################################
1) To run the full program using your browser

In your terminal,

*********First run command to Run workers*****************************************************

python worker.py [PORT1#]

Open another duplicate terminal and nevigate to directory then run 
python worker.py [PORT2#]

If you want to run with more workers, you will have to run more command in seprate terminal and add more worker

***************************************************************************************

*********Second you should Run coordiator*****************************************************

Open another duplicate terminal and nevigate to directory then
Second you should Run coordiator to connect all worker which you ran first by running below command 
python coordinator.py [PORT3#t#] [localhost:PORT1#] [localhost:PORT2#]
 
***************************************************************************************

*********Third you should run webserver************************************************

Open another duplicate terminal and nevigate to directory then
Thirdly you should run webserver to connect to coordinator by running below command
Make sure that port# for webserver should be same with coordinator's port, which is PORT3#
python webserver.py [PORT3#]

***************************************************************************************

*********Open browser in your computer************************************************

You will have to type 
webserver's port# is by default set to 8888, you should not use any other port when you are testing on browser
hostname:8888

HOST would be [whatever birdname you have for host].cs.umanitoba.ca
for example type >>>
crow.cs.umanitoba.ca:8888

***************************************************************************************

#########################################################################################


2) To test program with shellscript 

*********First run command to Run workers*****************************************************

python worker.py [PORT1#]

Open another duplicate terminal and nevigate to directory then run 
python worker.py [PORT2#]

If you want to run with more workers, you will have to run more command in seprate terminal and add more worker

***************************************************************************************

*********Second you should Run coordiator*****************************************************

Open another duplicate terminal and nevigate to directory then
Second you should Run coordiator to connect all worker which you ran first by running below command 
python coordinator.py [PORT3#t#] [localhost:PORT1#] [localhost:PORT2#]
 
***************************************************************************************

*********Third you .sh file provided in directoryr************************************************

Open another duplicate terminal and nevigate to directory then
Make sure that you will have to pass coordinator's port# while running shell script
To run shell script 
loadtest1.sh [PORT3#]
or 
loadtest2.sh [PORT3#]

***************************************************************************************



