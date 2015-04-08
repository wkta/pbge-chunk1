import gears
import container
import calibre

part = gears.BeamWeapon(name="Intercept Laser",reach=2,damage=1,accuracy=2,penetration=1)
print( isinstance( part, gears.Weapon ) )

my_mecha = gears.Mecha( desig="SAN-X9", name="Buru Buru", sub_com = (
        gears.Head(size=5, sub_com = (
            gears.Armor(size=4),
            gears.BeamWeapon(name="Intercept Laser",reach=2,damage=1,accuracy=2,penetration=1),
            gears.Sensor(),
        )),
        gears.Torso(size=5, sub_com = (
            gears.Armor(size=4),
            gears.Engine(size=605),
            gears.Gyroscope(),
            gears.Cockpit( sub_com = (
                gears.Armor(size=2),
            )),
            gears.Mount(name="Collar Mount", inv_com=(
                gears.Launcher( size=4, sub_com = (
                    gears.Missile( name="Swarm Missiles", reach=6,damage=1,accuracy=1,penetration=1,quantity=20 ),
                )),
            )),
        )),
        gears.Arm(name="Right Arm",size=5, sub_com = (
            gears.Armor(size=4),
            gears.Hand(name="Right Hand", inv_com=(
                gears.BallisticWeapon(name="Shaka Cannon",reach=5,damage=3,accuracy=0,penetration=3,sub_com=(
                    gears.Ammo( calibre=calibre.Shells_150mm, quantity=15 ),
                )),
            )),
        )),
        gears.Arm(name="Left Arm",size=5, sub_com = (
            gears.Armor(size=4),
            gears.Hand(name="Left Hand", inv_com=(
                gears.MeleeWeapon(name="Axe",reach=1,damage=3,accuracy=1,penetration=2),
            )),
        )),
        gears.Leg(name="Right Leg",size=5, sub_com = (
            gears.Armor(size=4),
            gears.HoverJets(size=4),
        )),
        gears.Leg(name="Left Leg",size=5, sub_com = (
            gears.Armor(size=4),
            gears.HoverJets(size=4),
        )),
    )
 )

print "{} tons".format( my_mecha.mass / 10000.0 )
print "${}".format( my_mecha.cost )

my_mecha.termdump()
