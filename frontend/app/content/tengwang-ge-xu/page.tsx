import type { Metadata } from "next";

import TengwangExperience from "@/components/content/tengwang/TengwangExperience";

export const metadata: Metadata = {
  title: "滕王阁序互动文境 · 悟典",
  description: "拨动竖排文字珠帘，在滕王阁建筑与王勃名篇之间感受经典。",
};

export default function TengwangGeXuPage() {
  return (
    <div className="-mx-4 -my-8 sm:-mx-6 lg:-mx-8">
      <TengwangExperience />
    </div>
  );
}
