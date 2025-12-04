import csv

file = "data/voos_2021.csv"

with open(file, "r", encoding="latin1") as f:
    sample = f.read(2048)

print("Amostra do arquivo:\n")
print(sample[:500])
print("\n---")

dialect = csv.Sniffer().sniff(sample, delimiters=";,|\t")
print("Delimitador detectado:", repr(dialect.delimiter))



