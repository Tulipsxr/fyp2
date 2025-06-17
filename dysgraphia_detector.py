import numpy as np
import pandas as pd
import cv2
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import os

class DysgraphiaDetector:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False

    def load_dataset(self, csv_path):
        """
        Load the dataset from CSV file
        Args:
            csv_path: Path to the CSV file containing image paths and sentences
        Returns:
            X: List of feature dictionaries
            y: List of labels (0 for LPD, 1 for PD)
        """
        # Read CSV file
        df = pd.read_csv(csv_path)
        
        X = []
        y = []
        
        for _, row in df.iterrows():
            image_path = row['Image Path']
            # Extract label from path (LPD = 0, PD = 1)
            label = 1 if 'PD/' in image_path else 0
            
            # Load and preprocess image
            try:
                image = cv2.imread(image_path)
                if image is not None:
                    features = self.extract_features(image)
                    X.append(features)
                    y.append(label)
            except Exception as e:
                print(f"Error processing {image_path}: {str(e)}")
        
        return X, y

    def extract_features(self, handwriting_image):
        """
        Extract relevant features from handwriting image
        Args:
            handwriting_image: Input image of handwriting
        Returns:
            features: Dictionary of extracted features
        """
        # Convert image to grayscale if it's not already
        if len(handwriting_image.shape) == 3:
            gray = cv2.cvtColor(handwriting_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = handwriting_image

        # Basic image preprocessing
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Extract features
        features = {
            'line_spacing': self._calculate_line_spacing(binary),
            'letter_size_variation': self._calculate_letter_size_variation(binary),
            'writing_pressure': self._estimate_writing_pressure(binary),
            'letter_spacing': self._calculate_letter_spacing(binary),
            'slant_angle': self._calculate_slant_angle(binary),
            'baseline_deviation': self._calculate_baseline_deviation(binary)
        }

        return features

    def _calculate_line_spacing(self, binary_image):
        """Calculate average spacing between lines"""
        # Find contours of text lines
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) < 2:
            return 0.0
            
        # Get bounding boxes of contours
        boxes = [cv2.boundingRect(c) for c in contours]
        boxes.sort(key=lambda x: x[1])  # Sort by y-coordinate
        
        # Calculate average spacing between consecutive lines
        spacings = []
        for i in range(len(boxes)-1):
            current_bottom = boxes[i][1] + boxes[i][3]
            next_top = boxes[i+1][1]
            spacing = next_top - current_bottom
            if spacing > 0:
                spacings.append(spacing)
                
        return np.mean(spacings) if spacings else 0.0

    def _calculate_letter_size_variation(self, binary_image):
        """Calculate variation in letter sizes"""
        # Find contours of individual letters
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) < 2:
            return 0.0
            
        # Calculate areas of contours
        areas = [cv2.contourArea(c) for c in contours]
        
        # Calculate coefficient of variation
        return np.std(areas) / np.mean(areas) if np.mean(areas) > 0 else 0.0

    def _estimate_writing_pressure(self, binary_image):
        """Estimate writing pressure from image intensity"""
        # Calculate average intensity of non-zero pixels
        non_zero = binary_image[binary_image > 0]
        return np.mean(non_zero) if len(non_zero) > 0 else 0.0

    def _calculate_letter_spacing(self, binary_image):
        """Calculate spacing between letters"""
        # Find contours of individual letters
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) < 2:
            return 0.0
            
        # Get bounding boxes of contours
        boxes = [cv2.boundingRect(c) for c in contours]
        boxes.sort(key=lambda x: x[0])  # Sort by x-coordinate
        
        # Calculate average spacing between consecutive letters
        spacings = []
        for i in range(len(boxes)-1):
            current_right = boxes[i][0] + boxes[i][2]
            next_left = boxes[i+1][0]
            spacing = next_left - current_right
            if spacing > 0:
                spacings.append(spacing)
                
        return np.mean(spacings) if spacings else 0.0

    def _calculate_slant_angle(self, binary_image):
        """Calculate the slant angle of writing"""
        # Find contours of text lines
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) < 2:
            return 0.0
            
        # Calculate angles of minimum area rectangles
        angles = []
        for c in contours:
            rect = cv2.minAreaRect(c)
            angle = rect[2]
            if angle < -45:
                angle += 90
            angles.append(abs(angle))
            
        return np.mean(angles) if angles else 0.0

    def _calculate_baseline_deviation(self, binary_image):
        """Calculate deviation from baseline"""
        # Find contours of text lines
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) < 2:
            return 0.0
            
        # Get bounding boxes of contours
        boxes = [cv2.boundingRect(c) for c in contours]
        
        # Calculate y-coordinates of bottom points
        bottom_points = [box[1] + box[3] for box in boxes]
        
        # Calculate standard deviation of bottom points
        return np.std(bottom_points) if bottom_points else 0.0

    def train(self, X, y):
        """
        Train the model on labeled data
        Args:
            X: List of feature dictionaries
            y: List of labels (0 for LPD, 1 for PD)
        """
        # Convert feature dictionaries to numpy array
        X_array = np.array([list(x.values()) for x in X])
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X_array)
        
        # Train model
        self.model.fit(X_scaled, y)
        self.is_trained = True

    def predict(self, handwriting_image):
        """
        Predict whether the handwriting shows signs of dysgraphia
        Args:
            handwriting_image: Input image of handwriting
        Returns:
            prediction: 0 (LPD) or 1 (PD)
            probability: Probability of dysgraphia
        """
        if not self.is_trained:
            raise ValueError("Model needs to be trained before making predictions")

        # Extract features
        features = self.extract_features(handwriting_image)
        
        # Convert features to numpy array and scale
        X = np.array([list(features.values())])
        X_scaled = self.scaler.transform(X)
        
        # Make prediction
        prediction = self.model.predict(X_scaled)[0]
        probability = self.model.predict_proba(X_scaled)[0][1]
        
        return prediction, probability

    def save_model(self, model_path, scaler_path):
        """Save the trained model and scaler"""
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)

    def load_model(self, model_path, scaler_path):
        """Load a trained model and scaler"""
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.is_trained = True

# Example usage
if __name__ == "__main__":
    # Create detector instance
    detector = DysgraphiaDetector()
    
    # Load and preprocess dataset
    X, y = detector.load_dataset('image_sentences.csv')
    
    # Train the model
    detector.train(X, y)
    
    # Save the model
    detector.save_model('dysgraphia_model.joblib', 'dysgraphia_scaler.joblib')
    
    # Example of making predictions
    """
    # Load an image
    test_image = cv2.imread('path_to_test_image.jpg')
    
    # Make prediction
    prediction, probability = detector.predict(test_image)
    print(f"Prediction: {'Potential Dysgraphia' if prediction == 1 else 'Low Potential Dysgraphia'}")
    print(f"Probability: {probability:.2%}")
    """ 