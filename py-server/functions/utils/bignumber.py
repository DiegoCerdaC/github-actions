from decimal import Decimal


def float_to_bignumber_string(number: float, decimals: int) -> str:
    # Convert float to Decimal
    decimal_number = Decimal(str(number))

    # Shift the decimal point to the appropriate position
    shifted_number = decimal_number * (10**decimals)

    # Convert to integer and then to a string
    big_number_string = str(int(shifted_number))

    return big_number_string
