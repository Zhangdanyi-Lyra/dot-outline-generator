# 新主体转换

先查看用户原图和 `approved-gray.png`，必要时打开对应预览了解真实透明效果。用户原图仅决定造型，基准图仅决定渲染。对照片优先保留识别物品所需的轮廓、部件和孔洞；不要追踪背景、摄影阴影或无关表面噪点。

先生成中性灰阶、真正透明的母版。显式设置 `transparent_background: true`。所有输入有本地路径时使用 `referenced_image_paths`；不要同时提供最近图片计数。生成后在当前任务目录保存母版和提示词，换色走脚本。

以下提示词中的主体描述应按用户图像替换；不要把本技能的示例角色写进新任务：

```text
Use case: style-transfer.
Create one transparent hollow outline artwork of the SUBJECT in reference 1,
rendered in the approved STYLE of reference 2.

Reference 1 is the geometry source. Preserve [describe the actual subject,
its proportions, pose, connected parts, overlaps and real holes].
Keep the complete subject and intentional asymmetries with transparent margins.
Do not invent anatomy, accessories, lettering or numbered labels.

Reference 2 supplies only the rendering treatment: a slightly hand-drawn
black outer edge with broad gray airbrush shading diffusing inward.
Do not copy its character, pose or composition.

The edge cross-section is:
TRANSPARENT EXTERIOR -> HAND-DRAWN BLACK OUTER EDGE -> DARK GRAY ->
LIGHTER GRAINY GRAY INWARD FADE -> TRANSPARENT INTERIOR.
The gray inside boundary dissolves directly into transparency.
No additional thin black, gray or white inner contour, inset ring, inner bevel,
parallel outline or separate highlight strip. Keep necessary subject structure
lines, but do not trace a second line along the inside of each shaded band.

Match the reference's broad, soft, uneven inward spray coverage.
Fine random scanned-print grain is denser near the outer edge and increasingly
sparse inward. Keep large open transparent areas. Gentle pressure variation
and small natural wavering belong only to the outer boundary.
Avoid symmetric inflated tubes, chrome, plastic, fabric, ropes, crosshatching,
regular repeated noise and large dirty patches.

Convert large filled faces in the source into transparent interiors.
Keep both the exterior background and the enclosed interiors genuinely transparent.
Black and neutral gray only. No solid backing, floor shadow or baked checkerboard.
Return one complete transparent PNG.
```

检查时先看实际 alpha 合成预览。发现内圈细线或圆管感，针对“内侧直接消散”和“单侧喷绘”修正。用户已确认的内部不要被后续“增加手绘感”整图重绘替换；转入局部编辑流程。

这是一套生成式风格转换，不能把参考图中的像素保真当作新主体生成的保证。相同母版的局部修改和换色才可以用像素比较验证。
