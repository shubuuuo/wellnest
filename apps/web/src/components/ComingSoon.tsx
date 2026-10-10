import Card from "./Card";

export default function ComingSoon({
  title,
  stage,
}: {
  title: string;
  stage: string;
}) {
  return (
    <Card title={title}>
      <p className="text-sm text-muted">This section is built in {stage}.</p>
    </Card>
  );
}
