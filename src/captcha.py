import cv2
import numpy as np
import pytesseract
import re
import Levenshtein
from sklearn.cluster import KMeans

double_digit_numbers = {
    'ده': 10,
    'یازده': 11,
    'دوازده': 12,
    'سیزده': 13,
    'چهارده': 14,
    'پانزده': 15,
    'شانزده': 16,
    'هفده': 17,
    'هجده': 18,
    'نوزده': 19,
    'بیست': 20,
    'سی': 30,
    'چهل': 40,
    'پنجاه': 50,
    'شصت': 60,
    'هفتاد': 70,
    'هشتاد': 80,
    'نود': 90,
    'صد': 100
    }
single_digit_numbers = {
    'صفر': 0,
    'یک': 1,
    'دو': 2,
    'سه': 3,
    'چهار': 4,
    'پنج': 5,
    'شش': 6,
    'هفت': 7,
    'هشت': 8,
    'نه': 9
    }
single_digit_numbers_with_and = {
    'صفر': 0,
    'یک': 1,
    'دو': 2,
    'سه': 3,
    'چهار': 4,
    'پنج': 5,
    'شش': 6,
    'هفت': 7,
    'هشت': 8,
    'نه': 9,
    'و': 'and'
    }
operations = {
    'منهای': '-',
    'بعلاوه': '+'
    }
def find_closest_word(target_word : str, dictionary : dict):
    closest_word = None
    min_distance = float('inf')
    for word in dictionary:
        distance = Levenshtein.distance(target_word, word)
        if distance < min_distance:
            min_distance = distance
            closest_word = dictionary[word]
    return closest_word, min_distance

def persian_only(s : str):
    return "".join(re.findall(r"[\u0600-\u06FF]+", s))

def find_operation(words : list):
    min_distance = float('inf')
    operation = None
    operation_idx = -1
    for idx, word in enumerate(words):
        closest_word, distance = find_closest_word(word, operations)
        if closest_word:
            if distance < min_distance:
                operation = closest_word
                min_distance = distance
                operation_idx = idx

    if min_distance > 5:
        return None, None
    return operation, operation_idx

def extract_text(image):
    text = pytesseract.image_to_string(image, lang='fas', config='--psm 7')
    words = text.split()
    persian_words = []
    for word in words:
        only_persian = persian_only(word)
        if only_persian:
            persian_words.append(only_persian)
    return persian_words

def interpret_text(words : list):
    operation, operation_idx = find_operation(words)
    if operation is None:
        print("Operation not found.")
        return None, None, None
    if operation_idx == 0 or operation_idx == len(words) - 1:
        print("One of the operators is missing.")
        return None, None, None
    first_operand = []
    for i, word in enumerate(words[:operation_idx]):
        if i == 0:
            closest_word, _ = find_closest_word(word, double_digit_numbers)
        else:
            closest_word, _ = find_closest_word(word, single_digit_numbers_with_and)
        if closest_word:
            first_operand.append(closest_word)
    second_operand = []
    for word in words[operation_idx+1:]:
        closest_word, _ = find_closest_word(word, single_digit_numbers)
        if closest_word:
            second_operand.append(closest_word)
    return first_operand, second_operand, operation

def interpret_first_operand(operand : list):
    op = None
    if len(operand) > 3:
        if 'and' in operand and operand.index('and') > 0 and operand.index('and') < len(operand) - 1:
            operand = operand[operand.index('and')-1:operand.index('and')+2]
        else:
            operand = operand[:3]
    if len(operand) == 1 and operand[0] != 'and':
        op = operand[0]
    elif len(operand) == 2:
        tmp = 0
        for word in operand:
            if word != 'and':
                tmp += word
        if tmp > 0:
            op = tmp
    elif len(operand) == 3:
        if 'and' in operand:
            tmp = 0
            for word in operand:
                if word != 'and':
                    tmp += word
            if tmp > 0:
                op = tmp
        else:
            op = operand[0] + operand[2]
    return op

def do_operation(first_operand : list, second_operand : list, operation : str):
    first_op = interpret_first_operand(first_operand)
    second_op = second_operand[0]

    if first_op is not None and second_op is not None:
        if operation == '+':
            return first_op + second_op
        else:
            return first_op - second_op

def filter_colors(image):
    lower_color = np.array([0, 0, 78])
    upper_color = np.array([255, 45, 255])
    threshold = 70
    temp = image[8:29, :]
    hsv = cv2.cvtColor(temp, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_color, upper_color)
    result = temp.copy()
    result[mask==0] = (255, 255, 255)
    pixels = result.reshape(-1, 3)
    num_colors = 2
    kmeans = KMeans(n_clusters=num_colors)
    kmeans.fit(pixels)
    dominant_colors = kmeans.cluster_centers_
    white_index = np.argmin(np.linalg.norm(dominant_colors - [255, 255, 255], axis=1))
    dominant_colors = np.delete(dominant_colors, white_index, axis=0)
    for i, pixel in enumerate(pixels):
        distances = np.linalg.norm(dominant_colors - pixel, axis=1)
        if np.min(distances) > threshold:
            pixels[i] = [255, 255, 255]  # Set pixel color to white
    result = pixels.reshape(result.shape)
    return result

def solve_persian_math_captcha(input_path: str):
    image = cv2.imread(input_path)
    filtered_image = filter_colors(image)
    text = extract_text(filtered_image)
    first_operand, second_operand, operation = interpret_text(text)
    if first_operand and second_operand:
        return do_operation(first_operand, second_operand, operation)    
    text = extract_text(image)
    first_operand, second_operand, operation = interpret_text(text)
    if first_operand and second_operand:
        return do_operation(first_operand, second_operand, operation)    
    return None

if __name__ == '__main__':
    input_path = '/app/download10.jpeg'
    result = solve_persian_math_captcha(input_path)
    if result:
        print(f"Result: {result}")
    else:
        print("FAILED!")
