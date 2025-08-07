import React from "react";

export default function JudgmentTable({ judgments }) {
  if (!judgments.length) return <p>불러온 판단이 없습니다.</p>;

  return (
    <table className="w-full table-auto border border-gray-300 text-sm">
      <thead className="bg-gray-100">
        <tr>
          <th className="px-2 py-1">🕒 시각</th>
          <th className="px-2 py-1">요청</th>
          <th className="px-2 py-1">위험도</th>
          <th className="px-2 py-1">설명</th>
          <th className="px-2 py-1">태그</th>
        </tr>
      </thead>
      <tbody>
        {judgments.map((j, idx) => (
          <tr key={idx} className="border-t">
            <td className="px-2 py-1">{j.timestamp}</td>
            <td className="px-2 py-1">{j.user_request}</td>
            <td className="px-2 py-1 text-center">{j.risk_level}</td>
            <td className="px-2 py-1">{j.explanation?.slice(0, 80)}...</td>
            <td className="px-2 py-1">{j.tags?.join(", ")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
