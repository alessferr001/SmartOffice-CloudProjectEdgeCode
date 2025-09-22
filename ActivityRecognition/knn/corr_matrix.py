def check_correlated_features(matrix, threshold=0.9):

    columns_to_drop= []
    
    for i in range(len(matrix.columns)):
        for j in range(i):
            if abs(matrix.iloc[j,i]) > threshold:
                
                colname = matrix.columns[j]
                if not colname in columns_to_drop:
                    columns_to_drop.append(matrix.columns[i])
                    break
    
    return columns_to_drop