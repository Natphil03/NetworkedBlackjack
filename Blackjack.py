import random
import pickle


# The Card class definition
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


def startingGame(conn):
    # The type of suit
    suits = ["Spades", "Hearts", "Clubs", "Diamonds"]

    # The suit value
    suits_values = {"Spades": u"\u2664", "Hearts": u"\u2661", "Clubs": u"\u2667", "Diamonds": u"\u2662"}

    # The type of card
    cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

    # The card value
    cards_values = {"A": 11, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10,
                    "K": 10}

    # The deck of cards
    deck = []

    # Loop for every type of suit
    for suit in suits:

        # Loop for every type of card in a suit
        for card in cards:
            # Adding card to the deck
            deck.append(Card(suits_values[suit], card, cards_values[card]))

    blackjack_game(deck, conn)


def drawPlayerCards(player_cards, deck, player_score):
    player_card = random.choice(deck)
    player_cards.append(player_card)
    deck.remove(player_card)
    player_score += player_card.card_value
    return player_cards, deck, player_score


def drawDealerCards(dealer_cards, deck, dealer_score):
    dealer_card = random.choice(deck)
    dealer_cards.append(dealer_card)
    deck.remove(dealer_card)
    # Updating the dealer score
    dealer_score += dealer_card.card_value
    return dealer_cards, deck, dealer_score


# Function for a single game of blackjack
def blackjack_game(deck, conn):
    # Cards for both dealer and player
    player_cards = []
    dealer_cards = []

    # Scores for both dealer and player
    player_score = 0
    dealer_score = 0

    # Initial dealing for player and dealer
    while len(player_cards) < 2:

        # Randomly dealing a card
        player_cards, deck, player_score = drawPlayerCards(player_cards, deck, player_score)

        # In case both the cards are Ace, make the first ace value as 1 
        if len(player_cards) == 2:
            if player_cards[0].card_value == 11 and player_cards[1].card_value == 11:
                player_cards[0].card_value = 1
                player_score -= 10


        # Print player cards and score
        print("PLAYER CARDS: ")
        for card in player_cards:
            print(card.value)
        message = "PLAYER SCORE = " + str(player_score)
        print(message)

        input()

        dealer_cards, deck, dealer_score = drawDealerCards(dealer_cards, deck, dealer_score)

        # Print dealer cards and score, keeping in mind to hide the second card and score
        print("DEALER CARDS: ")
        print(dealer_cards[0])
        if len(dealer_cards) == 1:

            print("DEALER SCORE = ", dealer_score)
        else:

            print("DEALER SCORE = ", dealer_score - dealer_cards[-1].card_value)

        # In case both the cards are Ace, make the second ace value as 1
        if len(dealer_cards) == 2:
            if dealer_cards[0].card_value == 11 and dealer_cards[1].card_value == 11:
                dealer_cards[1].card_value = 1
                dealer_score -= 10

        input()

    # Player gets a blackjack   
    if player_score == 21:
        print("PLAYER HAS A BLACKJACK!!!!")
        print("PLAYER WINS!!!!")
        quit()

    # Print dealer and player cards
    # print("DEALER CARDS: ")
    # print(dealer_cards[0])
    # print("DEALER SCORE = ", dealer_score - dealer_cards[-1].card_value)

    print()

    # print("PLAYER CARDS: ")
    # for cards in player_cards:
    #     print(cards)
    # print("PLAYER SCORE = ", player_score)

    # Managing the player moves
    while player_score < 21:
        choice = input("Enter H to Hit or S to Stand : ")

        # Sanity checks for player's choice
        if len(choice) != 1 or (choice.upper() != 'H' and choice.upper() != 'S'):
            print("Wrong choice!! Try Again")

        # If player decides to HIT
        if choice.upper() == 'H':
            player_cards, deck, player_score = drawPlayerCards(player_cards, deck, player_score)
            # Updating player score in case player's card have ace in them
            count = 0
            while player_score > 21 and count < len(player_cards):
                if player_cards[count].card_value == 11:
                    player_cards[count].card_value = 1
                    player_score -= 10
                    count += 1
                else:
                    count += 1

            # Print player and dealer cards
            print("DEALER CARDS: ")
            for card in dealer_cards:
                print(card)
            print("DEALER SCORE = ", dealer_score - dealer_cards[-1].card_value)

            print()

            print("PLAYER CARDS: ")
            for card in player_cards:
                print(card)
            print("PLAYER SCORE = ", player_score)

        # If player decides to Stand
        if choice.upper() == 'S':
            break

    # Print player and dealer cards
    print("PLAYER CARDS: ")
    for card in player_cards:
        print(card)
    print("PLAYER SCORE = ", player_score)

    print()

    print("REVEALING THE CARDS....")

    print("DEALER CARDS: ")
    for cards in dealer_cards:
        print(cards)
    print("DEALER SCORE = ", dealer_score)

    # Check if player has a Blackjack
    if player_score == 21:
        print("PLAYER HAS A BLACKJACK")
        quit()

    # Check if player busts
    if player_score > 21:
        print("PLAYER BUSTED!!! GAME OVER!!!")
        quit()

    input()

    # Managing the dealer moves
    while dealer_score < 17:
        print("DEALER DECIDES TO HIT.....")

        dealer_cards, deck, dealer_score = drawDealerCards(dealer_cards, deck, dealer_score)

        # Updating player score in case player's card have ace in them
        count = 0
        while dealer_score > 21 and count < len(dealer_cards):
            if dealer_cards[count].card_value == 11:
                dealer_cards[count].card_value = 1
                dealer_score -= 10
                count += 1
            else:
                count += 1

        # print player and dealer cards
        print("PLAYER CARDS: ")
        for cards in player_cards:
            print(cards)
        print("PLAYER SCORE = ", player_score)

        print()

        print("DEALER CARDS: ")
        for cards in dealer_cards:
            print(cards)
        print("DEALER SCORE = ", dealer_score)

        input()

    # Dealer busts
    if dealer_score > 21:
        print("DEALER BUSTED!!! YOU WIN!!!")
        quit()

    # Dealer gets a blackjack
    if dealer_score == 21:
        print("DEALER HAS A BLACKJACK!!! PLAYER LOSES")
        quit()

    # TIE Game
    if dealer_score == player_score:
        print("PUSH (TIE)!!")
        quit()

    # Player Wins
    elif player_score > dealer_score:
        print("PLAYER WINS!!!")
        quit()

    # Dealer Wins
    else:
        print("DEALER WINS!!!")
        quit()


#if __name__ == '__main__':
 #   startingGame()
