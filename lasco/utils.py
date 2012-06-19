"""Various utilities."""

import os


def repr_as_table(headers, *args):
    """Return a string that represents the given headers and arguments
    as a table.

    >>> print repr_as_table(['Name'], [])
    +------+
    | Name |
    +------+
    >>> print repr_as_table(['First name', 'Last name'],
    ...                     ['Jimmy', 'Robert', 'Enrico'],
    ...                     ['Page', 'Plant', 'Iglesias'])
    +------------+-----------+
    | First name | Last name |
    +------------+-----------+
    | Jimmy      | Page      |
    +------------+-----------+
    | Robert     | Plant     |
    +------------+-----------+
    | Enrico     | Iglesias  |
    +------------+-----------+
    """
    assert len(headers) == len(args)
    copies = [[headers[i]] + args[i] for i in range(len(args))]
    max_lengths = [max([len(x) for x in arg]) for arg in copies]
    row_sep = '+-'
    for i in range(len(max_lengths)):
        row_sep += '-' * max_lengths[i]
        row_sep += '-+-'
    row_sep = row_sep[:-1]  # remove extra '-' added in the loop

    lines = [row_sep]
    for i in range(len(copies[0])):
        line = '| '
        for j in range(len(copies)):
            line += copies[j][i].ljust(max_lengths[j]) + ' | '
        line = line[:-1]  # remove extra space added in the loop
        lines.append(line)
        lines.append(row_sep)
    return os.linesep.join(lines)
