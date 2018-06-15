import pbge
from pbge import Singleton
import geffects
import scale
import stats
import aitargeters


class TargetAnalysis(Singleton):
    name = 'Target Analysis'
    USE_AT = (scale.HumanScale, scale.MechaScale)
    COST = 100

    @classmethod
    def get_invocations(cls, pc):
        progs = list()

        myprog = pbge.effects.Invocation(
            name='Long Range Scan',
            fx=geffects.CheckConditions([aitargeters.TargetIsEnemy(), aitargeters.TargetIsHidden()],
                                        anim=geffects.SearchAnim, on_success=[
                    geffects.OpposedSkillRoll(stats.Perception, stats.Computers, stats.Speed, stats.Stealth,
                                              roll_mod=25, min_chance=25,
                                              on_success=[geffects.SetVisible(anim=geffects.SmokePoof, )],
                                              ), ]),
            area=pbge.scenes.targetarea.SelfCentered(radius=15, delay_from=-1),
            used_in_combat=True, used_in_exploration=True,
            ai_tar=aitargeters.GenericTargeter(targetable_types=(pbge.scenes.PlaceableThing,),
                                               conditions=[aitargeters.TargetIsOperational(),
                                                           aitargeters.TargetIsEnemy(),
                                                           aitargeters.TargetIsHidden()]),
            shot_anim=geffects.OriginSpotShotFactory(geffects.SearchTextAnim),
            data=geffects.AttackData(pbge.image.Image('sys_skillicons.png', 32, 32), 6),
            price=[],
            targets=1)
        progs.append(myprog)
        return progs


class Deflect(Singleton):
    name = 'Deflect'
    USE_AT = (scale.MechaScale,)
    COST = 200

    @classmethod
    def get_invocations(cls, pc):
        pass


class EMPPulse(Singleton):
    name = 'EM Pulse'
    USE_AT = (scale.HumanScale, scale.MechaScale,)
    COST = 200

    @classmethod
    def get_invocations(cls, pc):
        pass
