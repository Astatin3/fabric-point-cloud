package com.example;

import com.mojang.serialization.*;
import it.unimi.dsi.fastutil.objects.Reference2ObjectArrayMap;
import net.minecraft.block.BlockState;
import net.minecraft.block.Blocks;
import net.minecraft.particle.DustParticleEffect;
import net.minecraft.particle.ParticleEffect;
import net.minecraft.particle.ParticleType;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.registry.RegistryKey;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;
import net.minecraft.util.math.Vec3i;
import net.minecraft.world.World;
import org.joml.Vector3f;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.Map;
import java.util.stream.Stream;

public class testThread extends Thread {
    private Map<RegistryKey<World>, ServerWorld> worlds;
    private short[][] points = new short[2300][6];

    BufferedReader reader;
//    PrintWriter writer;


    public testThread(Map<RegistryKey<World>, ServerWorld> worlds) {
        this.worlds = worlds;
        startCommandThread();

    }

    private void startCommandThread() {
        Thread commandThread = new Thread(() -> {
//            BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
            String line;
            String[] split;
            int i = 0;
            try {
                ServerSocket serverSocket;
                serverSocket = new ServerSocket(65000, 50, InetAddress.getByName("127.0.0.1"));
                System.out.println("Server is listening on port " + (65000+i));

                while (true) {
                    Socket socket = serverSocket.accept();

                    System.out.println("New client connected");

                    InputStream input = socket.getInputStream();
//                    OutputStream output = socket.getOutputStream();

                    reader = new BufferedReader(new InputStreamReader(input));
//                    writer = new PrintWriter(output, true);

//                    line = reader.readLine();

                    while(socket.isConnected()) {
                        line = reader.readLine();
                        if(line == null || line.isEmpty()) {continue;}
                        split = line.split(",");
                        short[] point = new short[6];

                        int pointnum = Integer.parseInt(split[0]);
//                        System.out.println(pointnum);
                        points[pointnum] = point;

                        point[0] = Short.parseShort(split[1]);
                        point[1] = Short.parseShort(split[2]);
                        point[2] = Short.parseShort(split[3]);
                        point[3] = Short.parseShort(split[4]);
                        point[4] = Short.parseShort(split[5]);
                        point[5] = Short.parseShort(split[6]);


                    }

                    socket.close();
                    System.out.println("client disconnected");

//                    reader.next
                }

            } catch (Exception e) {
                e.printStackTrace();
            }
        });
        commandThread.setName("Point Cloud Thread");
        commandThread.setDaemon(true);
        commandThread.start();
    }

    public void run() {
        while(true){
            try {
                Thread.sleep(100);
            } catch (InterruptedException e) {e.printStackTrace();}

            if(!worlds.containsKey(World.OVERWORLD))
                continue;

            ServerWorld world = worlds.get(World.OVERWORLD);

            for(int i=0; i < points.length; i++) {
                if(points[i] == null) {continue;}
//                System.out.println(points[i][0]/100. + ", " + points[i][1]/100. + ", " + points[i][2]/100.);
//
                int rgb =          Math.clamp(points[i][5], 0, 255);
                rgb = (rgb << 8) + Math.clamp(points[i][4], 0, 255);
                rgb = (rgb << 8) + Math.clamp(points[i][3], 0, 255);

                world.spawnParticles(
                        new DustParticleEffect(Vec3d.unpackRgb(rgb).toVector3f(), 0.2F),
//                        new DustParticleEffect(DustParticleEffect.RED, 0.5F),
                        points[i][0]*0.02,
                        (points[i][2]*0.02) + 128,
                        points[i][1]*0.02,
                        10,
                        0,
                        0,
                        0,
                        0
                );
            }

        }
    }
}

