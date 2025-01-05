def main():
    keyboard = [
        list('1234567890'),
        list('qwertyuiop'),
        list('asdfghjkl'),
        list('zxcvbnm'),
    ]

    singles = [c for row in keyboard for c in row]
    doubles = [''.join(row[i:i+2]) for row in keyboard for i in range(len(row) - 1)]
    triples = [''.join(row[i:i+3]) for row in keyboard for i in range(len(row) - 2)]
    sixtets = [''.join(row[i:i+6]) for row in keyboard for i in range(len(row) - 5)]

    twice = [x * 2 for x in singles + doubles + triples]
    trice = [x * 3 for x in singles + doubles + triples]

    data = singles + doubles + triples + sixtets + twice + trice
    for k in keyboard: data.append(''.join(k))

    with open('../ddd/data/keyboard_patterns.txt', 'w') as f:
        f.write('\n'.join(data))

    print('ok')


if __name__ == '__main__':
    main()