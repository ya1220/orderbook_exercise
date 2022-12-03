from csv import reader
import sys
import datetime

DEBUG = False   #prints detailed messages if switched on

#Global storage containers
OUTPUT_LOG = [] #storage of output messages - for testing
orderbooks = { #'ticker': orderbook,
}

#Aliases
NEW_ORDER = 'N'
CANCEL_ORDER = 'C'
FLUSH_ORDERS = 'F'
order_types = [NEW_ORDER,CANCEL_ORDER,FLUSH_ORDERS]

ACCEPT_ORDER = 'A'
CROSS_ORDER = 'B'
REJECT_ORDER = 'R'
TRADE_ORDER = 'T'
BEST_CHANGE = 'B'
order_result_types = [ACCEPT_ORDER,BEST_CHANGE,CROSS_ORDER,REJECT_ORDER,TRADE_ORDER]

BID = 'B'
ASK = 'S'

CROSSING_BOOK_ENABLED = False

def read_input():
    filename = 'input_file.csv'
    inputs = []

    with open(filename, 'r') as inputfile:
        csv_reader = reader(inputfile)
        for row in csv_reader:
            if len(row) > 0:
                if row[0] in order_types:
                    inputs.append(row)
    return inputs

def read_test_cases():
    filename = 'output_file.csv'
    tests = []

    with open(filename, 'r') as inputfile:
        csv_reader = reader(inputfile)
        for row in csv_reader:
            if len(row) > 0:
                if row[0] in order_result_types:
                    if row[0] == ACCEPT_ORDER:
                        r = [row[0].strip(), int(row[1].strip()), int(row[2].strip())]
                    if row[0] == REJECT_ORDER:
                        r = [row[0].strip(), int(row[1].strip()), int(row[2].strip())]
                    if row[0] == BEST_CHANGE:
                        if row[2].strip() != '-':
                            r = [row[0].strip(), row[1].strip(), float(row[2].strip()),float(row[3].strip())]
                        else:
                            r = [row[0].strip(), row[1].strip(), '-', '-']
                    if row[0] == TRADE_ORDER:
                        r = [row[0].strip(), int(row[1].strip()), int(row[2].strip()),int(row[3].strip()),int(row[4].strip()),int(row[5].strip()),int(row[6].strip())]
                    tests.append(r)
    return tests

class order:
    def __init__(self,order_input_list):
        order_type = order_input_list[0]

        if order_type in order_types:
            self.order_type = order_type

            self.order_status = []
            self.userid = None
            self.symbol = None
            self.price = None
            self.qty = None
            self.side = None
            self.userOrderId = None

            if order_type == NEW_ORDER:
                if len(order_input_list) < 7: print("ERROR: invalid order type")
                # N, user(int),symbol(string),price(int),qty(int),side(char B or S),userOrderId(int)
                # N, 1, IBM, 10, 100, B, 1
                self.userid = int(order_input_list[1].strip())
                self.symbol = order_input_list[2].strip()
                self.price = float(order_input_list[3].strip())
                self.qty = float(order_input_list[4].strip())
                self.side = str(order_input_list[5].strip())
                self.userOrderId = int(order_input_list[6].strip())
            if order_type == CANCEL_ORDER:
                # C, 2, 102
                self.userid = int(order_input_list[1].strip())
                self.userOrderId = int(order_input_list[2].strip())
            if order_type == FLUSH_ORDERS:
                # F
                ...
        else:
            print("ERROR: invalid order type")
        return

    def print_order(self):
        print('ORDER: ', self.order_type,self.userid,self.symbol,self.price,self.qty,self.side,self.userOrderId)
        return

    def print_status(self):
        latest_status = self.order_status[len(self.order_status)-1]
        for i in range(len(latest_status)):
            print(latest_status[i], end = '')
            if i < len(latest_status)-1: print(', ', end = '')
        print()
        return


class orderbook():
    def __init__(self,order):
        if order.order_type != FLUSH_ORDERS:
            if DEBUG: print("INITIALISING ORDERBOOK FOR SYMBOL: ", order.symbol)
            print("-----------------")
        self.symbol = order.symbol

        self.book = {
            BID: [], #tuples of (time,order)
            ASK: [],
        }

        self.send_order(order)
        return

    def get_best_order(self,type):
        if len(self.book[type]) > 0: return self.book[type][0][1].price
        return 0.0

    def send_order(self,order):
        if order.order_type == FLUSH_ORDERS:
            if DEBUG: print("FLUSHING ORDERBOOK: ", order.symbol)

            self.book = {
            BID: [],
            ASK: [],
        }

            if DEBUG: print(len(self.book[BID]))
            if DEBUG:
                for el in self.book[BID]: print(el[0])
            if DEBUG:
                for el in self.book[ASK]: print(el[0])
            return

        if order.order_type == CANCEL_ORDER:
            order_exists = False
            print("TRYING TO MATCH CXL ORDER: ", order.userid,order.userOrderId)
            matching_order = next((x for x in self.book[ASK] if x[1].userid == order.userid and x[1].userOrderId == order.userOrderId), None)

            print("try 1 to MATCH cxl: ", matching_order,order.userid,type(order.userid),order.userOrderId,type(order.userOrderId))
            if matching_order is not None:
                if DEBUG: print("FOUND ORDER TO CXL")
                cxl_order_side = ASK
                order_exists = True
            else:
                matching_order = next(
                    (x for x in self.book[BID] if x[1].userid == order.userid and x[1].userOrderId == order.userOrderId),
                    None)
                cxl_order_side = BID
                print("try 2 to MATCH cxl: ", matching_order,order.userid,type(order.userid),order.userOrderId,type(order.userOrderId))
                if matching_order is not None: order_exists = True

            if order_exists:
                #change_to_bbo_after_cancelation = False
                best_BID_price_before_cancelation = self.book[BID][0][1].price
                best_ASK_price_before_cancelation = self.book[ASK][0][1].price

                best_volume_total_before_cxl = 0.0
                for i in range(len(self.book[cxl_order_side])):
                    if self.book[cxl_order_side][i][1].price == self.get_best_order(cxl_order_side):
                        best_volume_total_before_cxl += self.book[cxl_order_side][i][1].qty

                if DEBUG: print("SENDING CXL ACK: ",order.symbol)
                s = [ACCEPT_ORDER,order.userid,order.userOrderId]
                order.order_status.append(s)
                OUTPUT_LOG.append(s)

                #delete order from bids or asks
                if DEBUG: print("LEN BEFORE: ")
                if DEBUG: print("ASK: ", len(self.book[ASK]))
                if DEBUG: print("BID: ", len(self.book[BID]))

                for i in range(len(self.book[cxl_order_side])):
                    if self.book[cxl_order_side][i][1].userid == order.userid and self.book[cxl_order_side][i][1].userOrderId == order.userOrderId:
                        self.book[cxl_order_side].pop(i)
                        break

                best_BID_price_after_cancelation = self.get_best_order(BID)
                best_ASK_price_after_cancelation = self.get_best_order(ASK)

                order.print_status()

                #if BBO px changed
                if best_BID_price_before_cancelation != best_BID_price_after_cancelation or best_ASK_price_before_cancelation != best_ASK_price_after_cancelation:
                    if len(self.book[cxl_order_side]) > 0:
                        s = [BEST_CHANGE, cxl_order_side, self.get_best_order(cxl_order_side), self.book[cxl_order_side][0][1].qty]
                        order.order_status.append(s)
                        OUTPUT_LOG.append(s)
                        order.print_status()
                        return
                    else:
                        s = [BEST_CHANGE, cxl_order_side, '-', '-']
                        order.order_status.append(s)
                        OUTPUT_LOG.append(s)
                        order.print_status()
                        return

                #if BBO volume changed
                best_volume_total_after_cxl = 0.0
                for i in range(len(self.book[cxl_order_side])):
                    if self.book[cxl_order_side][i][1].price == self.get_best_order(cxl_order_side):
                        best_volume_total_after_cxl += self.book[cxl_order_side][i][1].qty

                if best_volume_total_before_cxl != best_volume_total_after_cxl:
                    s = [BEST_CHANGE, cxl_order_side, self.get_best_order(cxl_order_side),best_volume_total_after_cxl]
                    order.order_status.append(s)
                    OUTPUT_LOG.append(s)
                    order.print_status()

                return
            else:
                print("SENDING REJECTION - TRYING TO CANCEL NONEXISTENT ORDER")
                s = [REJECT_ORDER,order.userid,order.userOrderId]
                order.order_status.append(s)
                OUTPUT_LOG.append(s)
                return

        if order.order_type == NEW_ORDER:
            attempt_to_trade_at_price_worse_than_best = False
            if order.side == BID:
                if len(self.book[ASK]) > 0:
                    if order.price > self.get_best_order(ASK): attempt_to_trade_at_price_worse_than_best = True
            if order.side == ASK:
                if len(self.book[BID]) > 0:
                    if order.price < self.get_best_order(BID): attempt_to_trade_at_price_worse_than_best = True


            if attempt_to_trade_at_price_worse_than_best:
                print("ATTEMPT TO TRADE AT PX WORSE THAN BEST")
                s = [REJECT_ORDER,order.userid,order.userOrderId]
                order.order_status.append(s)
                OUTPUT_LOG.append(s)
                if DEBUG: order.print_order()
                order.print_status()
                return


            matched_or_no = False

            if DEBUG:
                if len(self.book[BID]) > 0 and len(self.book[ASK]) > 0:
                    print("order type: ", order.order_type,self.book[BID][0][1].price, order.price)
                    print("order type: ", order.order_type,self.book[ASK][0][1].price, order.price)

            if len(self.book[BID]) > 0 and len(self.book[ASK]) > 0:
                if order.side == ASK and self.book[BID][0][1].price == order.price: matched_or_no = True
                if order.side == BID and self.book[ASK][0][1].price == order.price: matched_or_no = True

            if matched_or_no:
                if CROSSING_BOOK_ENABLED:
                    if DEBUG: print("SENDING TRADE MATCHED: ")
                    if order.order_type == ASK: amt = min(order.qty,self.book[BID][0][1].qty)
                    if order.order_type == BID: amt = min(order.qty,self.book[ASK][0][1].qty)
                    if DEBUG: print("AMT TO MATCH: ", amt)
                    s = [TRADE_ORDER,order.userIdBuy, userOrderIdBuy, userIdSell, userOrderIdSell, price, quantity]
                    order.order_status.append(s)
                    OUTPUT_LOG.append(s)
                    if DEBUG: order.print_order()
                    order.print_status()
                    self.book[BID][0][1].qty -= amt
                    if self.book[BID][0][1].qty == 0.0: #if zero amount left - delete
                        self.book[BID].pop()
                    order.qty -= amt
                    if order.qty > 0.0:
                        self.book[order.side].append((datetime.datetime.now(), order))
                    else:
                        print("ORDER ALREADY MATCHED: nothing to append")
                    self.book[order.side] = sorted(self.book[BID], key=lambda x: x[1].price,reverse=True)  # lowest FIRST = ASKS
                    self.book[order.side] = sorted(self.book[ASK], key=lambda x: x[1].price,reverse=False)  # lowest FIRST = ASKS
                    return
                else:
                    s = [REJECT_ORDER, order.userid, order.userOrderId]
                    order.order_status.append(s)
                    OUTPUT_LOG.append(s)
                    if DEBUG: order.print_order()
                    order.print_status()
                    return

        change_top_of_the_book_or_no = False
        if DEBUG: print("is ask: ", order.side == ASK, "best ask: ", self.get_best_order(ASK)," order px: ", order.price)
        if DEBUG: print("is bid: ", order.side == BID, "best ask: ", self.get_best_order(BID)," order px: ", order.price)

        if order.side == BID and order.price >= self.get_best_order(BID):
            change_top_of_the_book_or_no = True

        if order.side == BID and self.get_best_order(BID) == 0.0:
            change_top_of_the_book_or_no = True

        if order.side == ASK and order.price <= self.get_best_order(ASK):
            change_top_of_the_book_or_no = True

        if order.side == ASK and self.get_best_order(ASK) == 0.0:
            change_top_of_the_book_or_no = True

        #no special cases - acknowledge order
        if DEBUG: print("SENDING ACK FOR NEW ORDER", order.order_type, order.symbol,'CHG: ', change_top_of_the_book_or_no)
        order.print_order()
        s = [ACCEPT_ORDER, order.userid, order.userOrderId]
        order.order_status.append(s)
        OUTPUT_LOG.append(s)
        order.print_status()

        if DEBUG: print("self.book[order.side] Keys: ", list(self.book.keys()))
        if DEBUG: print("self.book[order.side] type: ", type(self.book[order.side]))

        is_order_combining_with_existing_bbo = False
        if order.side == ASK and order.price == self.get_best_order(ASK): is_order_combining_with_existing_bbo = True
        if order.side == BID and order.price == self.get_best_order(BID): is_order_combining_with_existing_bbo = True

        #if is_order_combining_with_existing_bbo == False:
        self.book[order.side].append((datetime.datetime.now(), order))

        if DEBUG: print("REORDERING ORDERS")
        if DEBUG: order.print_order()

        rev = False
        if order.side == BID: rev = True
        self.book[order.side] = sorted(self.book[order.side], key=lambda x: x[1].price, reverse=rev)  # lowest FIRST = ASKS

        if change_top_of_the_book_or_no:
            if DEBUG: print("CHANGE TO BBO")

            if is_order_combining_with_existing_bbo:
                best_volume_total_after_insertion = 0.0
                for i in range(len(self.book[order.side])):
                    if self.book[order.side][i][1].price == self.get_best_order(order.side):
                        best_volume_total_after_insertion += self.book[order.side][i][1].qty

                s = [BEST_CHANGE,order.side,order.price, best_volume_total_after_insertion] #order.qty+self.book[order.side][0][1].qty
            else:
                s = [BEST_CHANGE,order.side,order.price, self.book[order.side][0][1].qty]
            order.order_status.append(s)
            OUTPUT_LOG.append(s)
            order.print_status()
            return

        return



if __name__ == '__main__':
    inputs = read_input()
    orders = []
    for input in inputs: orders.append(order(input))

    most_recent_symbol = None
    sc = 1

    for order in orders:
        if order.order_type == FLUSH_ORDERS:
            orderbooks[most_recent_symbol].send_order(order)  #FLUSH
            sc += 1
            print("----------------------", sc)
            continue
        if order.order_type == CANCEL_ORDER:
            if DEBUG: print("CXL RECEIVED")
            if DEBUG: order.print_order()
            orderbooks[most_recent_symbol].send_order(order)  #FLUSH
            continue
        if order.symbol not in list(orderbooks.keys()):
            if DEBUG: print("symbol: ", order.symbol)
            orderbooks[order.symbol] = orderbook(order)
            most_recent_symbol = order.symbol
        else:
            orderbooks[order.symbol].send_order(order)
            most_recent_symbol = order.symbol

        if DEBUG:
            print("LATEST BOOK: ")
            for el in orderbooks[most_recent_symbol].book[BID]:
                el[1].print_order()
            for el in orderbooks[most_recent_symbol].book[ASK]:
                el[1].print_order()

    #TESTS
    print("TESTS:")
    tests = read_test_cases()
    passes = 0
    scenario = 1
    print(len(tests), len(OUTPUT_LOG))
    for i in range(len(OUTPUT_LOG)):
        p = tests[i] == OUTPUT_LOG[i]
        if tests[i] == ['A',1,1]:
            print('---',scenario)
            scenario += 1
        print("TEST: ", tests[i], "         OUTPUT: ", OUTPUT_LOG[i], '     MATCH: ', p)
        if p: passes += 1

    print("TEST SUMMARY: ", passes, ' out of ', len(OUTPUT_LOG), ' cases passed')

