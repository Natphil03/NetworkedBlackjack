import random
import threading
import Connection
import time


class Card:
    def __init__(self, suit, value, card_value):
        # Suit of the Card like Spades and Clubs
        self.suit = suit
        # Representing Value of the Card like A for Ace, K for King
        self.value = value
        # Score Value for the Card like 10 for King
        self.card_value = card_value

    def __str__(self):
        return str(self.value)

    def __bytes__(self):
        return str(self.value)

class BlackJack:
    def __init__(self):
        self.suits = None
        self.values = None
        self.cards = None
        self.cards_values = None
        self.deck = None
        self.conn = None
        self.addr = None
        self.PlayerScore = 0
        self.DealerScore = 0
        self.PlayerCards = []
        self.DealerCards = []

    def startingGame(self, conn, addr, pubkey, privkey):
        self.conn = conn
        self.addr = addr
        # create connection and start thread
        self.connection = Connection.ConnectionClass()

        self.connThread = threading.Thread(target=self.connection.handle_client,
                                           args=(self.conn, self.addr, pubkey, privkey), daemon=True)

        self.connThread.start()
        # outline global variables
        time.sleep(3)
        # The type of suit
        self.suits = ["Spades", "Hearts", "Clubs", "Diamonds"]
        # The suit value
        self.suits_values = {"Spades": u"\u2664", "Hearts": u"\u2661", "Clubs": u"\u2667", "Diamonds": u"\u2662"}
        # The type of card
        self.cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        # The card value
        self.cards_values = {"A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
                             "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10}
        # The deck of cards
        self.deck = []
        # Loop for every type of suit
        for suit in self.suits:
            # Loop for every type of card in a suit
            for card in self.cards:
                # Adding card to the deck
                self.deck.append(Card(self.suits_values[suit], card, self.cards_values[card]))

        # start game
        self.blackjack_game()

    def drawPlayerCards(self):
        player_card = random.choice(self.deck)
        self.PlayerCards.append(player_card)
        self.deck.remove(player_card)
        self.PlayerScore += player_card.card_value

    def drawDealerCards(self):
        dealer_card = random.choice(self.deck)
        self.DealerCards.append(dealer_card)
        self.deck.remove(dealer_card)
        # Updating the dealer score
        self.DealerScore += dealer_card.card_value

    def states(self):
        time.sleep(2)
        # Player gets a blackjack
        if self.PlayerScore == 21:
            self.connection.sendMessage("PLAYER HAS A BLACKJACK!!!!")
            self.connection.sendMessage("PLAYER WINS!!!!")
            time.sleep(1)
            self.connection.sendMessage("QUIT")
            quit()
        # Check if player busts
        if self.PlayerScore > 21:
            self.connection.sendMessage("PLAYER BUSTED!!! GAME OVER!!!")
            time.sleep(1)
            self.connection.sendMessage("QUIT")
            quit()

        # Dealer busts
        if self.DealerScore > 21:
            self.connection.sendMessage("DEALER BUSTED!!! YOU WIN!!!")
            time.sleep(1)
            self.connection.sendMessage("QUIT")
            quit()

        # Dealer gets a blackjack
        if self.DealerScore == 21:
            self.connection.sendMessage("DEALER HAS A BLACKJACK!!! PLAYER LOSES")
            time.sleep(1)
            self.connection.sendMessage("QUIT")
            quit()

        # TIE Game
        if self.DealerScore == self.PlayerScore:
            self.connection.sendMessage("PUSH (TIE)!!")
            time.sleep(1)
            self.connection.sendMessage("QUIT")
            quit()


    def iteratePlayerCards(self):
        string = ''
        for card in self.PlayerCards:
            string += str(card.value) + ","
        self.connection.sendMessage("PLAYER CARDS: \n" + string + "\nPLAYER SCORE = " + str(self.PlayerScore))

    def iterateDealerCards(self):
        string = ''
        for card in self.DealerCards:
            string += str(card.value) + ","
        self.connection.sendMessage("DEALERS CARDS: \n" + string + "\nDEALER SCORE = " + str(self.DealerScore))

    def updatePlayerScore(self):
        # In case both the cards are Ace, make the first ace value as 1
        if len(self.PlayerCards) == 2:
            if self.PlayerCards[0].card_value == 11 and self.PlayerCards[1].card_value == 11:
                self.PlayerCards[0].card_value = 1
                self.PlayerScore -= 10

    def updateDealerScore(self):
        if len(self.DealerCards) == 2:
            if self.DealerCards[0].card_value == 11 and self.DealerCards[1].card_value == 11:
                self.DealerCards[1].card_value = 1
                self.DealerScore -= 10
        # In case both the cards are Ace, make the first ace value as 1

    # Function for a single game of blackjack
    def blackjack_game(self):
        while self.connection.connectedState:
            try:
                # Initial dealing for player and dealer
                while len(self.PlayerCards) < 2:
                    # Randomly dealing a card
                    self.drawPlayerCards()

                    self.updatePlayerScore()

                    self.iteratePlayerCards()

                    time.sleep(2)

                    self.drawDealerCards()
                    self.updateDealerScore()
                    # Print dealer cards and score, keeping in mind to hide the second card and score
                    self.iterateDealerCards()

                    time.sleep(2)

                self.states()

                # Print dealer and player cards
                self.iteratePlayerCards()

                time.sleep(2)
                self.iterateDealerCards()

                # Managing the player moves
                while self.PlayerScore < 21:
                    self.connection.sendMessage("Enter H to Hit or S to Stand or QUIT: ")

                    # informs client to enter
                    self.connection.sendMessage("[PlayerInputState]")
                    self.connection.playerInputState = True

                    choice = self.connection.getPlayerInput()# get message from custom buffer
                    self.connection.playerInputState = False

                    self.connection.sendMessage("[EndPlayerInputState]")# inform client to change states
                    time.sleep(5)
                    print("Choice: ", choice)

                    # If player decides to HIT
                    if choice.upper() == 'H':
                        self.drawPlayerCards()
                        # Updating player score in case player's card have ace in them
                        count = 0
                        self.updatePlayerScore()

                        # Print player and dealer cards
                        self.iteratePlayerCards()
                        time.sleep(2)
                        self.iterateDealerCards()
                        time.sleep(2)
                        self.states()

                    # If player decides to Stand
                    if choice.upper() == 'S':
                        break

                    if choice.upper() == "QUIT":
                        self.connection.sendMessage("QUIT")
                        self.connection.connectedState = False
                        quit()

                # Print player and dealer cards
                self.iteratePlayerCards()
                time.sleep(2)
                self.connection.sendMessage("REVEALING THE CARDS....")
                time.sleep(2)
                self.iterateDealerCards()

                self.states()

                time.sleep(2)

                # Managing the dealer moves
                while self.DealerScore < 17:
                    self.connection.sendMessage("DEALER DECIDES TO HIT.....")
                    self.drawDealerCards()

                    # Updating player score in case player's card have ace in them
                    count = 0
                    while self.DealerScore > 21 and count < len(self.DealerCards):
                        if self.DealerCards[count].card_value == 11:
                            self.DealerCards[count].card_value = 1
                            self.DealerScore -= 10
                            count += 1
                        else:
                            count += 1

                    time.sleep(2)
                    # print player and dealer cards
                    self.iteratePlayerCards()

                    self.connection.sendMessage(" ")

                    self.iterateDealerCards()

                    time.sleep(2)
                    self.connection.sendMessage(" ")

                    self.states()

                    # Player Wins
                    if self.PlayerScore > self.DealerScore:
                        self.connection.sendMessage("PLAYER WINS!!!")
                        time.sleep(1)
                        self.connection.sendMessage("QUIT")
                        quit()
                    else:
                        self.connection.sendMessage("DEALER WINS!!!")
                        time.sleep(1)
                        self.connection.sendMessage("QUIT")
                        quit()
            except Exception as e:
                print(e)
                self.connection.connectedState = False
