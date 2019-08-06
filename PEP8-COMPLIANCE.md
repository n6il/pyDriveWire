    for i in *.py; do autopep8 -v --in-place --aggressive --aggressive --ignore E501,E704,E731 ${i}; done

