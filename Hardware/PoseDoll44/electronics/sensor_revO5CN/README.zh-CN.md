# MT6701 + CJT 五线试验板

12×10×1 mm，两层板；最终 ERC、含原理图一致性的 DRC 为零违规，8 个 0.30/0.60 mm 过孔均避开 SMD 焊盘。`preview` 是最后一轮原生板导出的正反面图。

针脚 1…5：GND、3V3、CLK、DO、CSN。连接器是完整 CJT 配套，不能和旧 JST 六针按位置混接。节点侧 DO 隔离仍需要，区域板尚未改型。QFN EP 接法未获得原厂确认，目前为隔离铜岛，阻塞制造；无需据此下单或装机。封装尺寸及焊盘由原厂图重新建模，焊盘设计仍需厂家 DFM，未冒称官方 KiCad 库。

详细资料、供应商取舍和未完成项见 `Hardware/PoseDoll44/docs/CN_SUPPLIERS_AND_DESIGN.zh-CN.md`。没有生成制造放行 Gerber。
