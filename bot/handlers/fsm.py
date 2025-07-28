from aiogram.fsm.state import State, StatesGroup

class SimpleFlightSearch(StatesGroup):
    waiting_for_date = State()
    waiting_for_flight_number = State()

class FlightSearchStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_number = State() 