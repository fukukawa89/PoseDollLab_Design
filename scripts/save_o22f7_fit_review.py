from o22f7_animation import *
import datetime
p=WORK/'fit_review_browser_raw.txt';blob=p.read_bytes();text=blob.decode('utf-16') if blob.startswith(b'\xff\xfe') else blob.decode('utf-8-sig');actual=json.loads(text.split('### Result',1)[1].split('### Ran',1)[0].strip());assert not actual['errors'] and actual['played'] and actual['numerical']<1e-5 and actual['end']['error']<1e-5;assert actual['left']['playDisabled'] and not actual['left']['overflow'] and not actual['mobile']['overflow']
html=WORK/'锁骨装配路径复核.html';destination=B/'O22F7_锁骨装配复核_20261016.html';shutil.copy2(html,destination);assert sha(html)==sha(destination)
evidence=WORK/'fit_review_evidence';evidence.mkdir(exist_ok=True)
for name in ['clavicle_review_left.png','clavicle_review_right.png','clavicle_review_mobile.png']:shutil.copy2(R/'output/playwright'/name,evidence/name)
report={'passed_for_diagnostic_viewer':True,'full_tutorial_complete':False,'created_at':datetime.datetime.now().astimezone().isoformat(),'html':str(destination),'html_sha256':sha(html),'browser':actual,'motion_start_check':read(WORK/'fit_review_start_phase_check.json'),'source':read(WORK/'clavicle_fit_review.json'),'manufacturing_files_unchanged':164,'original_print_archive_sha256':sha(B/'O22F7_PLA_完整打印包_20261016.zip')};assert report['original_print_archive_sha256']=='d31a9999319bc94141d06b429c4e9464a1c1d4bf0da68b86ace308fce22e63e2';put(WORK/'fit_review_delivery.json',report)
write(WORK/'本轮装配复核记录.txt','''O22F7 装配动画复核 · 2026-10-16

用户确认：左右锁骨连接件尚未实际装配。尚未回答这两件是否已经打印。
完整任务仍未完成：原动画维持 26 章 / 1650 个动作的校核预览，S04、S11 仍设闸口，不发布最终版。

本轮有效进展：
右侧在裸胸部、左侧已装并转到 -20 度、左侧 8 件关节五金及右侧 3 件内侧五金已放好的条件下，找到完整候选路线。
路径文件：clavicle_right_parked_left_goal_0_1_path.json。
独立加密检查 right_parked_left_dense_review.json：2683 个采样，表面位移上界 0.25 mm，名义体积容差 0.02 mm3。此为指定场景的采样检查，非连续扫掠或实物公差认证。
左侧回到 0 度且右侧就位时，81 个角度采样无相交。
左侧回位后，头颈核心原侧向进入路径检查了 44 个活动件对 19 个已装件，91 个位置无相交。

左侧：尚无完整进入 / 退出路径。长路径可达前缀已通过部分加密检查，但不能把部分路线当成可装配证明。多种搜索未成功，也不证明绝对无法装配。
后续如继续保留现有零件，应继续寻找完整且可操作的左侧路线；如需结构修正，应先明确用户已打印情况，保护原有关节轴线、孔位、传感器位置和活动范围，并另行验证，不覆盖当前打印件。

右侧路线不能直接塞回旧 S11：需要把裸胸部与两侧连接件的预装前移，再接胸部核心和头颈。左侧问题解决前，不能把 S11 条件通过当成整套完成。
preassembly_interfaces_review 的两项失败涉及临时放在手边的半壳 / 摩擦垫。它们不是已固定障碍，不应据此宣布模型无法装配，但动画的临时摆放位置需要调整，避免视觉重叠。

已交付独立自包含 HTML 复核页，可以离线打开：左侧红色标出直推动作干涉，右侧显示带前提的候选动画。原教程未改为最终版。
原始 O22F7 打印 ZIP、164 个制造文件及既有教程验证文件校验均保持不变。
试验性的通用刚体动画渲染改动已保存为 rigid_renderer_experiment.js；正式动画源码 app.js 已恢复为当前已验证预览的版本。
页面检查：播放、暂停、进度切换、桌面和手机布局、最终位姿与 Python 的 5 个时刻对照均通过，无浏览器错误。详细结果 fit_review_delivery.json。
''')
print(json.dumps({'viewer':str(destination),'sha256':sha(destination),'browser_passed':True,'complete':False,'original_print_archive_unchanged':True},ensure_ascii=False))
