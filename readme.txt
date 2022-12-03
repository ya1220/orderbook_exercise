ARCHITECTURE
class orderbook:
    stores a symbol and a book dictionary.
    The book dictionary contains 2 keys: BID and ASK. To each of these keys maps a list of (time,order) tuples
    Book is ordered whereby index 0 represents the respective BID or ASK order:
        BID: highest bid is at index 0
        ASK: lowest ask = index 0

Orderbooks are stored in a global dictionary 'orderbooks' where keys are tickers

class order:
    stores the order parameters
            order_type
            order_status
            userid
            symbol
            price
            qty
            side
            userOrderId

            Default values for each parameter are 'None' - these are kept at none for order types which do not track price / quantity

read_input: function to read csv inputs
read_test_cases: function to read csv of test cases

main: 3 loops - one to read inputs, one to process the orders, and one for tests

Aliasing
    Each order type string is assigned an alias - i.e. ASK is the alias for 'B'

OUTPUT_LOG
    Stores all order processing messages for testing

HOW TO RUN
    written in python 3.9
    To run: 'py main.py' / 'python3 main.py' / 'python3.x main.py' (if using specific python version) depending on Linux/Windows
    Dependencies: csv,datetime - both part of standard library, no installation of new modules is required
    To create docker image: docker build --tag orderbook .
    To run docker image: docker run orderbook

POTENTIAL IMPROVEMENTS:
    There are a couple of loops which can be turned into list comprehensions: for calculating total volume on the best BID/ASK
    Order crossing function to aggregate volume available across all orders - for the case where several orders at one price are best
    Mechanics for rejecting orders at above best price - to be executed at the best price instead with a message to inform user on that
    Splitting up the test cases into a list where each list element is a scenario - right now everything is read as one big array and split is manual whenever a ['A',1,1] comes up - which isn't fully accurate
    Enabling command line inputs to read custom input files and write to a custom output file
    Reducing number of loops in main to reduce time complexity
    Changing the OUTPUT_LOG object from global to a class member variable - as part of 'orderbooks' class (changing orderbooks from dictionary to class)