# About WellNest

WellNest is a student machine-learning demo that estimates cancer risk from patient data. It is for education only and is not a medical diagnosis or medical advice.

# The five tabs

The Dataset tab shows the data: row counts, the balance between cancer and non-cancer cases in a pie chart, and histograms of each input.

The Models tab compares six trained models using accuracy, precision, recall, F1 and ROC-AUC, plus a confusion matrix for the best model.

The Predict tab takes patient details in a form and returns an estimated risk percentage from the best model that outputs probabilities.

The Online Learning tab replays patient rows in small chunks. Online models update after every chunk and a live chart shows their test score rising or staying flat.

The Assistant tab is this chatbot. It answers questions about the app, its data and its scores.

# Online and batch models

An online model can learn from a few new rows at a time without starting over. In this app the online models are SGD Logistic Regression, SGD Linear SVM, Gaussian Naive Bayes and the Neural Network (MLP). They update their internal numbers using a method called partial fit.

A batch-only model cannot learn from a few new rows. To use new data it must be retrained from scratch on all data. In this app Random Forest and the RBF-kernel SVM are batch-only. The Online Learning tab shows their scores trained on the small starting set and after a full batch retrain.

Online learning is enabled here for course demonstration. It is not recommended for real clinical use, because bad or wrong data can silently make a model worse.

# How data is split

20 percent of the rows are kept as a test set that no model ever learns from. About 10 percent of all rows form a small starting set used to train the starting models. The remaining rows, about 70 percent, are the stream: they are released in chunks during the online learning demo.

# Metrics explained

Accuracy is the share of all predictions that are correct. It can mislead when one class is much bigger than the other, because always guessing the big class already scores high.

Precision is how many of the patients flagged as cancer really had cancer. Recall (also called sensitivity) is how many of the real cancer cases were found. Missing a real case is usually worse than a false alarm, so recall matters a lot in screening.

F1 is a single number that balances precision and recall. ROC-AUC measures how well a model ranks risky patients above safe ones, from 0.5 (random) to 1.0 (perfect).

The confusion matrix counts true negatives, false alarms (false positives), missed cancers (false negatives) and true positives.

# Limits

The datasets are public Kaggle tables and may be synthetic, so scores do not reflect real-world performance. Risk estimates are probabilities from a statistical model, not a diagnosis. Anyone worried about their health should see a qualified clinician.