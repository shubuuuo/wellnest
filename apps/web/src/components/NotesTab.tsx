import Card from "./Card";

export default function NotesTab() {
  return (
    <div className="space-y-6">
      <Card title="Models and how they learn">
        <ul className="list-disc space-y-1 pl-5 text-sm">
          <li>
            <b>Online:</b> SGD Logistic Regression, SGD Linear SVM, Gaussian
            Naive Bayes, Neural Network (MLP). They can update from new rows
            without starting over.
          </li>
          <li>
            <b>Batch only:</b> Random Forest and RBF-kernel SVM. They must be
            retrained on all data.
          </li>
        </ul>
      </Card>
      <Card title="Important">
        <ul className="list-disc space-y-1 pl-5 text-sm">
          <li>
            Online learning is enabled for course demonstration. It is not
            recommended for real clinical use.
          </li>
          <li>
            The dataset is a public Kaggle table and may be synthetic. Scores do
            not reflect real-world performance.
          </li>
          <li>This is an educational estimate, not a medical diagnosis.</li>
        </ul>
      </Card>
    </div>
  );
}
