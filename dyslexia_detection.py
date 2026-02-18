from flask import Flask, request, jsonify
import numpy as np

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    age = data["Age"]
    gender = label_encoders["Gender"].transform([data["Gender"]])[0]
    nativelang = label_encoders["Nativelang"].transform([data["Nativelang"]])[0]
    game_stats = np.array(data["GameStats"]).reshape(1, -1)

    # Normalize input
    game_stats_scaled = scaler.transform(game_stats)

    # Predict
    prediction = model.predict(game_stats_scaled)[0]
    result = "Dyslexia Detected" if prediction == 1 else "No Dyslexia Detected"

    return jsonify({"prediction": result})

if __name__ == '__main__':
    app.run(debug=True)
