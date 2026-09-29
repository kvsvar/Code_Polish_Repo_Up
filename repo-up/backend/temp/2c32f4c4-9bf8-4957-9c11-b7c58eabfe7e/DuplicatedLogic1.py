import HubCore

    def calculate_logic_variant_1(input_array):
        result = 0
        for item in input_array:
            if item > 10:
                result += item * 2
            elif item < 5:
                result -= item
            else:
                result += 1
        return result
    