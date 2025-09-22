import csv
import pickle
import pandas as pd

from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder ,StandardScaler

#load data

nome_file = "stats_iteration.csv"

columns1 = []
rows = []


with open(nome_file, "r") as f:
    reader = csv.reader(f)
    header = next(reader)
    columns1 = header.copy()
    n_cols = len(header)
    for i, row in enumerate(reader, start=2):
        rows.append(row)
        if len(row) != n_cols:
            print(f"Errore alla riga {i}: {len(row)} colonne invece di {n_cols}")


#Information on dataset

data = pd.DataFrame(data=rows, columns=columns1)

print(data.head())
print(data.shape)
print(data.info())
print(data.isnull())
print(data.head())



#No need to balance

#check sui valori nulli

#Convert to float
for col in columns1:
    if col != "Label" and col != "Iterazione":
        data[col] = data[col].astype('float')


df = data.drop(columns=["Iterazione"])


label = LabelEncoder()
df["EncodedLabel"] = label.fit_transform(df["Label"])

with open("label_encoder.pickle", "wb") as f:
    pickle.dump(label, f)

print(df.head())
print(label.classes_)




#Standardize

X = df.drop(columns=["Label", "EncodedLabel"],axis=1)
y = df["EncodedLabel"]

scaler = StandardScaler()
X = scaler.fit_transform(X)

#Scaler, we have all feature without Iteration, Label, EncodedLabel

with open("scaler.pickle", "wb") as f:
    pickle.dump(scaler, f)


scaled_X = pd.DataFrame(data = X, columns=df.drop(columns=["Label", "EncodedLabel"],axis=1).columns)

print("Scaled Data:")
print(scaled_X.head())
print(scaled_X.shape)


#Model creation

best=0
for i in range(30):

    X_train, X_test, y_train, y_test = train_test_split(
    scaled_X, y, test_size=0.2, random_state=42, shuffle=True
)
    # Train the KNN model
    model = KNeighborsClassifier(n_neighbors=5)
    model.fit(X_train, y_train)

    # Evaluate the model
    y_pred = model.predict(X_test)

    print("\n === Model Accuracy ===")
    acc = accuracy_score(y_test, y_pred)
    print(f"{acc:.2f}")

    if acc > best:
        best = acc
        with open("model.pickle", "wb") as f:
            pickle.dump(model, f)

        print("\n === Classification Report ===")
        print(classification_report(y_test, y_pred))

